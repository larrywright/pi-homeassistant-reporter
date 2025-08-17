#!/usr/bin/env python3
"""
Pi System Monitor - Collects system metrics and publishes to MQTT for Home Assistant

Reads metrics from Node Exporter and publishes them to MQTT with Home Assistant discovery.
"""

import requests
import json
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import time
import socket
import re
import logging
from datetime import datetime
from config import *

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_hostname():
    """Get the system hostname"""
    return socket.gethostname()

def parse_node_exporter_metrics():
    """Parse Node Exporter metrics and extract the ones we care about"""
    try:
        response = requests.get(NODE_EXPORTER_URL, timeout=NODE_EXPORTER_TIMEOUT)
        response.raise_for_status()
        metrics_text = response.text
        
        metrics = {}
        
        # Use load average as CPU metric (more straightforward than calculating rates)
        load_match = re.search(r'node_load1 ([\d.e+-]+)', metrics_text)
        if load_match:
            metrics['cpu_load_1min'] = float(load_match.group(1))
        
        load5_match = re.search(r'node_load5 ([\d.e+-]+)', metrics_text)
        if load5_match:
            metrics['cpu_load_5min'] = float(load5_match.group(1))
        
        # Memory usage
        mem_total_match = re.search(r'node_memory_MemTotal_bytes ([\d.e+-]+)', metrics_text)
        mem_available_match = re.search(r'node_memory_MemAvailable_bytes ([\d.e+-]+)', metrics_text)
        if mem_total_match and mem_available_match:
            mem_total = float(mem_total_match.group(1))
            mem_available = float(mem_available_match.group(1))
            mem_used = mem_total - mem_available
            metrics['memory_used_percent'] = round((mem_used / mem_total) * 100, 1)
            metrics['memory_used_gb'] = round(mem_used / (1024**3), 2)
            metrics['memory_total_gb'] = round(mem_total / (1024**3), 2)
        
        # Disk usage for root filesystem
        disk_size_match = re.search(r'node_filesystem_size_bytes{.*mountpoint="/".*} ([\d.e+-]+)', metrics_text)
        disk_avail_match = re.search(r'node_filesystem_avail_bytes{.*mountpoint="/".*} ([\d.e+-]+)', metrics_text)
        if disk_size_match and disk_avail_match:
            disk_total = float(disk_size_match.group(1))
            disk_available = float(disk_avail_match.group(1))
            disk_used = disk_total - disk_available
            metrics['disk_used_percent'] = round((disk_used / disk_total) * 100, 1)
            metrics['disk_free_gb'] = round(disk_available / (1024**3), 2)
            metrics['disk_total_gb'] = round(disk_total / (1024**3), 2)
        
        # CPU Temperature (look for thermal zone or hwmon)
        temp_matches = re.findall(r'node_hwmon_temp_celsius{.*} ([\d.]+)', metrics_text)
        if temp_matches:
            # Usually the first one is CPU temp, but this can vary
            metrics['cpu_temp_celsius'] = round(float(temp_matches[0]), 1)
        else:
            # Try thermal zone
            thermal_matches = re.findall(r'node_thermal_zone_temp{.*} ([\d.]+)', metrics_text)
            if thermal_matches:
                metrics['cpu_temp_celsius'] = round(float(thermal_matches[0]) / 1000, 1)  # Convert from millidegrees
        
        # Network throughput for eth0
        eth0_rx_match = re.search(r'node_network_receive_bytes_total{device="eth0"} ([\d.]+)', metrics_text)
        eth0_tx_match = re.search(r'node_network_transmit_bytes_total{device="eth0"} ([\d.]+)', metrics_text)
        if eth0_rx_match:
            metrics['network_rx_bytes_total'] = int(float(eth0_rx_match.group(1)))
        if eth0_tx_match:
            metrics['network_tx_bytes_total'] = int(float(eth0_tx_match.group(1)))
        
        # Disk I/O
        disk_read_match = re.search(r'node_disk_read_bytes_total{device="mmcblk0"} ([\d.]+)', metrics_text)
        disk_write_match = re.search(r'node_disk_written_bytes_total{device="mmcblk0"} ([\d.]+)', metrics_text)
        if disk_read_match:
            metrics['disk_read_bytes_total'] = int(float(disk_read_match.group(1)))
        if disk_write_match:
            metrics['disk_write_bytes_total'] = int(float(disk_write_match.group(1)))
        
        # Uptime
        uptime_match = re.search(r'node_time_seconds ([\d.e+]+)', metrics_text)
        boot_time_match = re.search(r'node_boot_time_seconds ([\d.e+]+)', metrics_text)
        if uptime_match and boot_time_match:
            current_time = float(uptime_match.group(1))
            boot_time = float(boot_time_match.group(1))
            uptime_seconds = current_time - boot_time
            metrics['uptime_seconds'] = int(uptime_seconds)
            metrics['uptime_days'] = round(uptime_seconds / 86400, 1)
        
        logger.debug(f"Parsed {len(metrics)} metrics")
        return metrics
        
    except Exception as e:
        logger.error(f"Error parsing metrics: {e}")
        return {}

def publish_to_mqtt(metrics):
    """Publish metrics to MQTT with Home Assistant discovery"""
    hostname = get_hostname()
    
    try:
        client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=f"pi-monitor-{hostname}")
        
        # Set authentication if configured
        if MQTT_USERNAME and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Publish each metric
        for metric_name, value in metrics.items():
            # State topic
            state_topic = f"{hostname}/sensor/{metric_name}"
            client.publish(state_topic, str(value), retain=True)
            
            # Discovery topic for Home Assistant auto-discovery
            discovery_topic = f"{HA_DISCOVERY_PREFIX}/sensor/{hostname}_{metric_name}/config"
            
            # Configure the sensor based on metric type
            config = {
                "name": f"{hostname} {metric_name.replace('_', ' ').title()}",
                "state_topic": state_topic,
                "unique_id": f"{hostname}_{metric_name}",
                "device": {
                    "identifiers": [hostname],
                    "name": f"Raspberry Pi ({hostname})",
                    "manufacturer": "Raspberry Pi Foundation"
                }
            }
            
            # Add appropriate units and device classes
            if "percent" in metric_name:
                config["unit_of_measurement"] = "%"
            elif "celsius" in metric_name:
                config["unit_of_measurement"] = "°C"
                config["device_class"] = "temperature"
            elif "gb" in metric_name:
                config["unit_of_measurement"] = "GB"
            elif "seconds" in metric_name and "uptime" in metric_name:
                config["unit_of_measurement"] = "s"
            elif "days" in metric_name:
                config["unit_of_measurement"] = "days"
            elif "bytes_total" in metric_name:
                config["unit_of_measurement"] = "B"
            elif "load" in metric_name:
                config["unit_of_measurement"] = ""
                config["icon"] = "mdi:chip"
            
            client.publish(discovery_topic, json.dumps(config), retain=True)
        
        # Publish availability
        availability_topic = f"{hostname}/sensor/availability"
        client.publish(availability_topic, "online", retain=True)
        
        client.disconnect()
        logger.info(f"Published {len(metrics)} metrics to MQTT for {hostname}")
        
    except Exception as e:
        logger.error(f"Error publishing to MQTT: {e}")

def main():
    """Main loop"""
    hostname = get_hostname()
    logger.info(f"Starting Pi monitoring for {hostname}")
    logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"Update interval: {UPDATE_INTERVAL} seconds")
    
    while True:
        try:
            metrics = parse_node_exporter_metrics()
            if metrics:
                publish_to_mqtt(metrics)
            else:
                logger.warning("No metrics collected")
            
            time.sleep(UPDATE_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Stopping Pi monitoring")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(10)  # Wait before retrying

if __name__ == "__main__":
    main()