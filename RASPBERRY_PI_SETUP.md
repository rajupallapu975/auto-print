# 🍓 Raspberry Pi 4 Setup Guide

Complete guide to deploy the Auto-Print Module on Raspberry Pi 4 running Raspberry Pi OS (Linux).

---

## 📋 Prerequisites

### Hardware
- **Raspberry Pi 4** (2GB+ RAM recommended)
- **MicroSD Card** (16GB+ recommended)
- **USB Printer** connected to the Pi
- **Network Connection** (WiFi or Ethernet)
- **Power Supply** (Official 5V 3A USB-C recommended)

### Software
- **Raspberry Pi OS** (64-bit recommended, Lite or Desktop)
- **Python 3.7+** (pre-installed on Raspberry Pi OS)

---

## 🚀 Step-by-Step Installation

### 1. Initial Raspberry Pi Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system dependencies
sudo apt install -y python3-pip python3-venv git cups cups-client

# Enable and start CUPS (printer service)
sudo systemctl enable cups
sudo systemctl start cups
```

### 2. Configure CUPS for Printing

```bash
# Add your user to the lpadmin group (allows printer management)
sudo usermod -a -G lpadmin $USER

# Reboot to apply group changes
sudo reboot
```

After reboot, configure your printer:

```bash
# List available printers
lpstat -p -d

# If your printer isn't detected, add it manually via CUPS web interface:
# Open browser and go to: http://localhost:631
# Navigate to Administration > Add Printer
# Follow the wizard to add your USB printer
```

### 3. Transfer Project Files to Raspberry Pi

**Option A: Using Git (Recommended)**
```bash
# Clone your repository
cd ~
git clone <your-repo-url> auto-print
cd auto-print
```

**Option B: Using SCP from your Windows machine**
```powershell
# From your Windows machine (PowerShell)
scp -r d:\psfc\auto-print pi@<raspberry-pi-ip>:~/auto-print
```

**Option C: Using USB Drive**
```bash
# Copy files from mounted USB drive
cp -r /media/usb/auto-print ~/auto-print
cd ~/auto-print
```

### 4. Setup Python Virtual Environment

```bash
cd ~/auto-print

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

### 5. Configure Firebase Credentials

```bash
# Transfer your serviceAccountKey.json to the Pi
# You can use scp, USB drive, or manually create the file

# If using scp from Windows:
# scp d:\psfc\auto-print\serviceAccountKey.json pi@<raspberry-pi-ip>:~/auto-print/

# Verify the file exists
ls -la serviceAccountKey.json
```

### 6. Configure Backend URL

Edit `main.py` to point to your backend server:

```bash
nano main.py
```

Update the `BACKEND_BASE_URL`:
```python
# Change from localhost to your actual backend server IP/domain
BACKEND_BASE_URL = "http://<your-backend-server-ip>:5000"
# Example: "http://192.168.1.100:5000" or "https://your-domain.com"
```

### 7. Configure Printer Name (Optional)

```bash
# Find your printer name
lpstat -p -d

# Edit main.py and set PRINTER_NAME
nano main.py
```

Update the printer configuration:
```python
# Set to your printer name or leave as None for default
PRINTER_NAME = "Your_Printer_Name"  # Example: "HP_LaserJet_Pro"
```

### 8. Test the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the application
python main.py
```

---

## 🔧 Auto-Start on Boot (Optional)

To make the application start automatically when the Pi boots:

### Method 1: Using systemd (Recommended)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/auto-print.service
```

Add the following content:

```ini
[Unit]
Description=Auto-Print Module
After=network.target cups.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/auto-print
Environment="PATH=/home/pi/auto-print/venv/bin"
ExecStart=/home/pi/auto-print/venv/bin/python /home/pi/auto-print/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable auto-print.service

# Start the service now
sudo systemctl start auto-print.service

# Check status
sudo systemctl status auto-print.service

# View logs
sudo journalctl -u auto-print.service -f
```

### Method 2: Using crontab

```bash
# Edit crontab
crontab -e

# Add this line at the end:
@reboot sleep 30 && cd /home/pi/auto-print && /home/pi/auto-print/venv/bin/python main.py >> /home/pi/auto-print/logs/autoprint.log 2>&1
```

---

## 🛠️ Troubleshooting

### Printer Not Detected

```bash
# Check if printer is connected
lsusb

# Check CUPS status
sudo systemctl status cups

# Check printer queue
lpstat -p -d

# View CUPS error log
sudo tail -f /var/log/cups/error_log
```

### Python Module Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Network Connection Issues

```bash
# Check network connectivity
ping -c 4 google.com

# Check if backend is reachable
curl http://<your-backend-ip>:5000

# Check firewall (if enabled)
sudo ufw status
```

### Permission Errors

```bash
# Ensure user is in lpadmin group
groups $USER

# Add user to lpadmin if missing
sudo usermod -a -G lpadmin $USER

# Reboot after adding to group
sudo reboot
```

---

## 📊 Monitoring & Maintenance

### View Application Logs

```bash
# If running as systemd service
sudo journalctl -u auto-print.service -f

# If running manually, redirect output to log file
python main.py >> logs/autoprint.log 2>&1
```

### Update Application

```bash
cd ~/auto-print

# Pull latest changes (if using git)
git pull

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart service (if using systemd)
sudo systemctl restart auto-print.service
```

### Check System Resources

```bash
# CPU and memory usage
htop

# Disk space
df -h

# Temperature (important for Pi)
vcgencmd measure_temp
```

---

## 🔒 Security Best Practices

1. **Change Default Password**
   ```bash
   passwd
   ```

2. **Enable Firewall**
   ```bash
   sudo apt install ufw
   sudo ufw allow ssh
   sudo ufw enable
   ```

3. **Keep System Updated**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Secure Firebase Key**
   ```bash
   chmod 600 serviceAccountKey.json
   ```

---

## 🌐 Remote Access (Optional)

### SSH Access

```bash
# Enable SSH (if not already enabled)
sudo systemctl enable ssh
sudo systemctl start ssh

# Connect from another machine
ssh pi@<raspberry-pi-ip>
```

### VNC Access (For Desktop Version)

```bash
# Enable VNC
sudo raspi-config
# Navigate to: Interface Options > VNC > Enable
```

---

## 📝 Useful Commands

```bash
# Check Python version
python3 --version

# Check pip version
pip --version

# List installed Python packages
pip list

# Check printer status
lpstat -p -d

# Test print a file
lp -d <printer-name> test.pdf

# Restart CUPS
sudo systemctl restart cups

# View running processes
ps aux | grep python

# Kill the application
pkill -f main.py
```

---

## 🆘 Getting Help

If you encounter issues:

1. Check the logs: `sudo journalctl -u auto-print.service -f`
2. Verify printer connection: `lpstat -p -d`
3. Test network connectivity to backend
4. Ensure Firebase credentials are valid
5. Check Python dependencies are installed

---

## 📚 Additional Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [CUPS Documentation](https://www.cups.org/documentation.html)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
