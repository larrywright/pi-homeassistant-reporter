# Monitoring Multiple Raspberry Pis

This guide explains how to set up monitoring for multiple Raspberry Pis using the same MQTT broker and Home Assistant instance.

## Overview

Each Pi will:
- Run its own instance of the monitoring service
- Publish metrics using its hostname as the identifier
- Automatically create separate sensors in Home Assistant
- Be visible as a separate device in Home Assistant

## Setup Process

### 1. Prerequisites

Ensure all your Pis can reach your MQTT broker:
- All Pis on the same network as your MQTT broker, OR
- Firewall rules allowing MQTT traffic (port 1883) from Pi networks
- MQTT broker configured to accept connections from all Pi IPs

### 2. Deploy to Each Pi

On each Raspberry Pi:

```bash
# Clone the repository
git clone https://github.com/yourusername/pi-system-monitor.git
cd pi-system-monitor

# Configure MQTT broker (same for all Pis)
nano config.py
# Set MQTT_BROKER = "192.168.1.100"  # Your MQTT broker IP

# Install and start monitoring
make install
```

### 3. Verify Installation

Check that each Pi is publishing metrics:

```bash
# On each Pi, check service status
make status

# View logs to confirm metrics are being published
make logs
```

In your MQTT explorer, you should see topics like:
```
pi1/sensor/cpu_load_1min
pi1/sensor/memory_used_percent
pi2/sensor/cpu_load_1min
pi2/sensor/memory_used_percent
pi3/sensor/cpu_load_1min
pi3/sensor/memory_used_percent
```

### 4. Home Assistant Configuration

Each Pi will automatically appear as a separate device in Home Assistant under:
- **Settings** → **Devices & Services** → **MQTT** → **Devices**

You should see devices named:
- "Raspberry Pi (pi1)"
- "Raspberry Pi (pi2)" 
- "Raspberry Pi (pi3)"
- etc.

## Creating Dashboard Cards

### Option 1: Individual Cards per Pi

Create separate dashboard cards for each Pi by copying `homeassistant-card.yaml` and replacing the hostname:

**For Pi named "pi1":**
```yaml
# Replace all instances of "radio" with "pi1"
entity: sensor.raspberry_pi_pi1_pi1_cpu_load_1min
```

**For Pi named "pi2":**
```yaml
# Replace all instances of "radio" with "pi2"  
entity: sensor.raspberry_pi_pi2_pi2_cpu_load_1min
```

### Option 2: Multi-Pi Overview Card

Create a summary card showing key metrics from all Pis:

```yaml
type: entities
title: 🖥️ All Raspberry Pis
show_header_toggle: false
entities:
  - type: section
    label: "Pi 1 (Living Room)"
  - entity: sensor.raspberry_pi_pi1_pi1_cpu_load_1min
    name: CPU Load
    icon: mdi:chip
  - entity: sensor.raspberry_pi_pi1_pi1_memory_used_percent
    name: Memory
    icon: mdi:memory
  - entity: sensor.raspberry_pi_pi1_pi1_cpu_temp_celsius
    name: Temperature
    icon: mdi:thermometer
  - type: section
    label: "Pi 2 (Garage)"
  - entity: sensor.raspberry_pi_pi2_pi2_cpu_load_1min
    name: CPU Load
    icon: mdi:chip
  - entity: sensor.raspberry_pi_pi2_pi2_memory_used_percent
    name: Memory
    icon: mdi:memory
  - entity: sensor.raspberry_pi_pi2_pi2_cpu_temp_celsius
    name: Temperature
    icon: mdi:thermometer
  - type: section
    label: "Pi 3 (Workshop)"
  - entity: sensor.raspberry_pi_pi3_pi3_cpu_load_1min
    name: CPU Load
    icon: mdi:chip
  - entity: sensor.raspberry_pi_pi3_pi3_memory_used_percent
    name: Memory
    icon: mdi:memory
  - entity: sensor.raspberry_pi_pi3_pi3_cpu_temp_celsius
    name: Temperature
    icon: mdi:thermometer
```

### Option 3: Auto-Entities Card

Use the `auto-entities` custom card to automatically include all Pi sensors:

```yaml
type: custom:auto-entities
card:
  type: entities
  title: 🖥️ All Pi CPU Temperatures
show_empty: false
filter:
  include:
    - entity_id: "sensor.raspberry_pi_*_cpu_temp_celsius"
      options:
        name: "{{state_attr(config.entity, 'friendly_name').split(' ')[2]}} CPU Temp"
sort:
  method: entity_id
```

## Useful Automations

### High Temperature Alert

Get notified when any Pi runs hot:

```yaml
alias: "Pi High Temperature Alert"
trigger:
  - platform: numeric_state
    entity_id: 
      - sensor.raspberry_pi_pi1_pi1_cpu_temp_celsius
      - sensor.raspberry_pi_pi2_pi2_cpu_temp_celsius
      - sensor.raspberry_pi_pi3_pi3_cpu_temp_celsius
    above: 70
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "⚠️ Pi Overheating"
      message: "{{trigger.to_state.attributes.friendly_name}} is running at {{trigger.to_state.state}}°C"
```

### Weekly Pi Status Report

Get a weekly summary of all your Pis:

```yaml
alias: "Weekly Pi Status Report"
trigger:
  - platform: time
    at: "09:00:00"
  - platform: time_pattern
    weekday: 1  # Monday
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "📊 Weekly Pi Report"
      message: |
        Pi Status Summary:
        🖥️ Pi1: {{states('sensor.raspberry_pi_pi1_pi1_uptime_days')|round(1)}} days uptime, {{states('sensor.raspberry_pi_pi1_pi1_cpu_temp_celsius')}}°C
        🖥️ Pi2: {{states('sensor.raspberry_pi_pi2_pi2_uptime_days')|round(1)}} days uptime, {{states('sensor.raspberry_pi_pi2_pi2_cpu_temp_celsius')}}°C  
        🖥️ Pi3: {{states('sensor.raspberry_pi_pi3_pi3_uptime_days')|round(1)}} days uptime, {{states('sensor.raspberry_pi_pi3_pi3_cpu_temp_celsius')}}°C
```

## Troubleshooting Multiple Pis

### Pi Not Appearing in Home Assistant

1. **Check MQTT topics**: Use MQTT Explorer to verify the Pi is publishing
2. **Check hostname**: Ensure each Pi has a unique hostname
3. **Restart Home Assistant**: Sometimes needed for MQTT discovery
4. **Check MQTT broker logs**: Look for connection issues

### Duplicate Entity IDs

If you see entity ID conflicts:
1. Ensure each Pi has a unique hostname: `sudo hostnamectl set-hostname newname`
2. Restart the monitoring service: `make status && sudo systemctl restart pi-monitor`
3. Clear Home Assistant entity registry if needed

### Performance Considerations

For many Pis (10+):
- Consider increasing `UPDATE_INTERVAL` in `config.py` to 120+ seconds
- Monitor your MQTT broker performance
- Use QoS 0 for metrics that don't need guaranteed delivery

### Network Issues

If some Pis can't reach the MQTT broker:
- Test connectivity: `telnet your-mqtt-broker 1883`
- Check firewall rules on both Pi and broker sides
- Consider using MQTT over TLS for remote Pis

## Maintenance

### Updating All Pis

Create a simple script to update all Pis:

```bash
#!/bin/bash
# update-all-pis.sh

PI_HOSTS=("pi1.local" "pi2.local" "pi3.local")

for host in "${PI_HOSTS[@]}"; do
    echo "Updating $host..."
    ssh pi@$host "cd pi-system-monitor && git pull && make install"
done
```

### Monitoring the Monitors

Create a Home Assistant sensor to track how many Pis are online:

```yaml
template:
  - sensor:
      - name: "Pis Online Count"
        state: >
          {{ states.sensor 
             | selectattr('entity_id', 'match', 'sensor\.raspberry_pi_.*_availability')
             | selectattr('state', 'eq', 'online')
             | list | count }}
        icon: mdi:raspberry-pi
```

## Best Practices

1. **Consistent Naming**: Use descriptive hostnames (e.g., `living-room-pi`, `garage-pi`)
2. **Documentation**: Keep a list of what each Pi does and where it's located
3. **Monitoring**: Set up alerts for when Pis go offline
4. **Updates**: Keep the monitoring software updated across all Pis
5. **Backups**: Include the monitoring config in your Pi backup strategy

## Example: 3-Pi Home Setup

Here's a real-world example of monitoring 3 Pis:

- **`living-room-pi`**: Media center, monitors TV cabinet temperature
- **`garage-pi`**: Security cameras, monitors garage door sensors  
- **`workshop-pi`**: 3D printer controller, monitors enclosure temperature

Each publishes both system metrics (via this tool) and custom sensors (temperature, door status, etc.) to the same MQTT broker, creating a comprehensive home monitoring system in Home Assistant.