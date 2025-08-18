# Pi System Monitor

A lightweight system monitoring solution for Raspberry Pi that collects system metrics and publishes them to MQTT for Home Assistant integration.

## Features

- 📊 **Comprehensive Metrics**: CPU load, memory usage, disk usage, temperature, network I/O, disk I/O, uptime
- 🏠 **Home Assistant Integration**: Automatic MQTT discovery creates sensors in Home Assistant
- 🔄 **Reliable**: Systemd service with automatic restart on failure
- 🚀 **Easy Setup**: Single command installation with Makefile
- 📱 **Dashboard Ready**: Includes pre-built Home Assistant dashboard card
- 🔧 **Lightweight**: Minimal resource usage, perfect for Pi Zero and up

## Prerequisites

- Raspberry Pi running Debian/Ubuntu with systemd
- Node Exporter installed (`sudo apt install prometheus-node-exporter`)
- MQTT broker accessible from your Pi
- Home Assistant with MQTT integration configured

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/pi-system-monitor.git
   cd pi-system-monitor
   ```

2. **Configure MQTT broker**:
   Copy the configuration template and edit it:
   ```bash
   cp config.py.template config.py
   nano config.py
   # Set MQTT_BROKER = "192.168.1.100"  # Replace with your MQTT broker IP
   ```

3. **Install and start the service**:
   ```bash
   make install
   ```

That's it! The service will start automatically and begin publishing metrics to MQTT.

## Configuration

### MQTT Settings

Copy the configuration template and customize your settings:

```bash
cp config.py.template config.py
```

Then edit `config.py` to configure your MQTT connection:

```python
# MQTT Configuration
MQTT_BROKER = "192.168.1.100"  # Your MQTT broker IP
MQTT_PORT = 1883
MQTT_USERNAME = None  # Set if authentication required
MQTT_PASSWORD = None  # Set if authentication required

# Update interval (seconds)
UPDATE_INTERVAL = 60

# Node Exporter URL
NODE_EXPORTER_URL = "http://localhost:9100/metrics"
```

### Home Assistant Dashboard

After installation, the metrics will automatically appear in Home Assistant. To add the dashboard card:

1. Go to your Home Assistant dashboard
2. Add a new card and select "Manual"
3. Copy the YAML from `homeassistant-card.yaml` (replace `radio` with your Pi's hostname)
4. Save the card

## Available Commands

```bash
make help        # Show available commands
make install     # Install the service and dependencies
make uninstall   # Remove the service and files  
make run         # Run the script directly (for testing)
make status      # Show service status
make logs        # Show service logs
make clean       # Clean up temporary files
```

## Metrics Collected

| Metric | Description | Unit |
|--------|-------------|------|
| CPU Load (1min/5min) | System load average | Load units |
| Memory Usage | RAM utilization | % and GB |
| Disk Usage | Root filesystem usage | % and GB |
| CPU Temperature | Processor temperature | °C |
| Network I/O | Total bytes RX/TX on eth0 | Bytes |
| Disk I/O | Total bytes read/written | Bytes |
| Uptime | System uptime | Seconds/Days |

## MQTT Topics

Metrics are published to topics following this pattern:
```
{hostname}/sensor/{metric_name}
```

For example, for a Pi with hostname "radio":
```
radio/sensor/cpu_load_1min
radio/sensor/memory_used_percent
radio/sensor/disk_free_gb
radio/sensor/cpu_temp_celsius
```

Home Assistant discovery topics are published to:
```
homeassistant/sensor/{hostname}_{metric_name}/config
```

## Troubleshooting

### Service not starting
```bash
# Check service status
make status

# View logs
make logs

# Test the script manually
make run
```

### No metrics in Home Assistant
1. Verify MQTT broker connection
2. Check Home Assistant MQTT integration is working
3. Ensure Node Exporter is running: `curl http://localhost:9100/metrics`

### Metrics showing as "unknown"
- Wait a few minutes for the first metrics to be collected
- Check if the Pi's hostname matches the entity names in Home Assistant

## Development

### Project Structure
```
pi-system-monitor/
├── Makefile                    # Build and deployment automation
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── config.py                   # Configuration settings
├── reporter.py                 # Main monitoring script
├── homeassistant-card.yaml     # HA dashboard card template
└── examples/
    └── multiple-pis.md         # Guide for monitoring multiple Pis
```

### Running for Development
```bash
# Create development environment
make run

# Or manually:
uv venv
uv pip install -r requirements.txt
.venv/bin/python reporter.py
```

## Multiple Pi Setup

To monitor multiple Raspberry Pis:

1. Deploy this repository to each Pi
2. Configure the same MQTT broker on all Pis
3. Each Pi will automatically create its own sensors using its hostname
4. Create separate dashboard cards for each Pi in Home Assistant

See `examples/multiple-pis.md` for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on a Raspberry Pi
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Uses [Node Exporter](https://github.com/prometheus/node_exporter) for system metrics collection
- Built for [Home Assistant](https://www.home-assistant.io/) MQTT integration
- Inspired by the need for simple, reliable Pi monitoring