#!/usr/bin/env python3
"""
Configuration file for Pi System Monitor
"""

# MQTT Configuration
MQTT_BROKER = "192.168.1.100"  # Replace with your MQTT broker IP
MQTT_PORT = 1883
MQTT_USERNAME = None  # Set if authentication required
MQTT_PASSWORD = None  # Set if authentication required

# Update interval (seconds)
UPDATE_INTERVAL = 60

# Node Exporter Configuration
NODE_EXPORTER_URL = "http://localhost:9100/metrics"
NODE_EXPORTER_TIMEOUT = 10

# Home Assistant MQTT Discovery
HA_DISCOVERY_PREFIX = "homeassistant"

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR