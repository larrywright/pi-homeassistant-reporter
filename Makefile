# Pi System Monitor - Makefile
# Collects system metrics and publishes to MQTT for Home Assistant

INSTALL_DIR = /opt/pi-monitor
SERVICE_NAME = pi-monitor
SERVICE_FILE = $(SERVICE_NAME).service
PYTHON_SCRIPT = reporter.py
CONFIG_FILE = config.py.template
USER = $(shell whoami)

.PHONY: help install uninstall run status logs clean check-deps check-config

help:
	@echo "Pi System Monitor - Available targets:"
	@echo "  install     - Install the service and dependencies"
	@echo "  uninstall   - Remove the service and files"
	@echo "  run         - Run the script directly (for testing)"
	@echo "  status      - Show service status"
	@echo "  logs        - Show service logs"
	@echo "  clean       - Clean up temporary files"
	@echo "  check-deps  - Check if required dependencies are available"
	@echo ""
	@echo "Before installing, copy config.py.template to config.py and edit your settings:"
	@echo "  cp config.py.template config.py && nano config.py"

check-config:
	@if [ ! -f config.py ]; then \
		echo "Creating config.py from template..."; \
		cp config.py.template config.py; \
		echo ""; \
		echo "⚠️  Please edit config.py and set your MQTT_BROKER before continuing!"; \
		echo "   nano config.py"; \
		echo ""; \
		exit 1; \
	fi
	@grep -q "192.168.1.100" config.py && { \
		echo "⚠️  Please update MQTT_BROKER in config.py before installing!"; \
		echo "   nano config.py"; \
		exit 1; \
	} || true

check-deps: check-config
	@echo "Checking dependencies..."
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	@command -v systemctl >/dev/null 2>&1 || { echo "ERROR: systemd not available"; exit 1; }
	@systemctl --version >/dev/null 2>&1 || { echo "ERROR: systemd not running"; exit 1; }
	@echo "Dependencies check passed"

install: check-deps
	@echo "Installing Pi System Monitor..."
	sudo mkdir -p $(INSTALL_DIR)
	sudo cp $(PYTHON_SCRIPT) $(INSTALL_DIR)/
	sudo cp config.py $(INSTALL_DIR)/
	sudo cp requirements.txt $(INSTALL_DIR)/
	sudo chown -R $(USER):$(USER) $(INSTALL_DIR)
	cd $(INSTALL_DIR) && uv venv
	cd $(INSTALL_DIR) && uv pip install -r requirements.txt
	@echo "Creating systemd service..."
	@echo '[Unit]' | sudo tee /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'Description=Pi System Metrics Monitor' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'After=network.target' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'Wants=network.target' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo '' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo '[Service]' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'Type=simple' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'User=$(USER)' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'Group=$(USER)' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'WorkingDirectory=$(INSTALL_DIR)' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'ExecStart=$(INSTALL_DIR)/.venv/bin/python -u $(INSTALL_DIR)/$(PYTHON_SCRIPT)' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'Restart=always' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'RestartSec=10' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'StandardOutput=journal' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'StandardError=journal' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo '' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo '[Install]' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	@echo 'WantedBy=multi-user.target' | sudo tee -a /etc/systemd/system/$(SERVICE_FILE) > /dev/null
	sudo systemctl daemon-reload
	sudo systemctl enable $(SERVICE_NAME)
	sudo systemctl start $(SERVICE_NAME)
	@echo ""
	@echo "Installation complete!"
	@echo "Service status:"
	@sudo systemctl status $(SERVICE_NAME) --no-pager -l

uninstall:
	@echo "Uninstalling Pi System Monitor..."
	-sudo systemctl stop $(SERVICE_NAME)
	-sudo systemctl disable $(SERVICE_NAME)
	-sudo rm -f /etc/systemd/system/$(SERVICE_FILE)
	sudo systemctl daemon-reload
	sudo rm -rf $(INSTALL_DIR)
	@echo "Uninstallation complete!"

run: check-config
	@echo "Running Pi System Monitor directly..."
	uv venv --quiet
	uv pip install -r requirements.txt --quiet
	.venv/bin/python $(PYTHON_SCRIPT)

status:
	@sudo systemctl status $(SERVICE_NAME) --no-pager -l

logs:
	@sudo journalctl -u $(SERVICE_NAME) -f

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf *.pyc
