# 🍓 Raspberry Pi Quick Reference

Quick reference for common commands and operations on your Raspberry Pi Auto-Print Module.

---

## 🚀 Starting the Application

### Manual Start
```bash
cd ~/auto-print
source venv/bin/activate
python main.py
```

### As Background Process
```bash
cd ~/auto-print
source venv/bin/activate
nohup python main.py > logs/autoprint.log 2>&1 &
```

### Using systemd Service
```bash
# Start
sudo systemctl start auto-print

# Stop
sudo systemctl stop auto-print

# Restart
sudo systemctl restart auto-print

# Status
sudo systemctl status auto-print

# Enable auto-start on boot
sudo systemctl enable auto-print

# Disable auto-start
sudo systemctl disable auto-print
```

---

## 🖨️ Printer Commands

### Check Printer Status
```bash
# List all printers
lpstat -p -d

# Check specific printer
lpstat -p YourPrinterName

# Check printer queue
lpq

# Check CUPS status
sudo systemctl status cups
```

### Test Print
```bash
# Print a test page
lp -d YourPrinterName /usr/share/cups/data/testprint

# Print a PDF file
lp -d YourPrinterName document.pdf

# Print with options
lp -d YourPrinterName -n 2 -o sides=two-sided-long-edge document.pdf
```

### Manage Print Queue
```bash
# View queue
lpq

# Cancel all jobs
cancel -a

# Cancel specific job
cancel job-id

# Clear printer queue
lprm -
```

### Configure Printer
```bash
# Add user to printer admin group
sudo usermod -a -G lpadmin $USER

# Access CUPS web interface
# Open browser to: http://localhost:631

# Restart CUPS
sudo systemctl restart cups
```

---

## 📊 Monitoring & Logs

### View Application Logs
```bash
# If running as systemd service
sudo journalctl -u auto-print.service -f

# View last 50 lines
sudo journalctl -u auto-print.service -n 50

# View logs since today
sudo journalctl -u auto-print.service --since today

# View logs from specific time
sudo journalctl -u auto-print.service --since "2026-02-03 10:00:00"
```

### System Monitoring
```bash
# CPU and memory usage
htop

# Disk space
df -h

# Disk usage by directory
du -sh *

# Temperature
vcgencmd measure_temp

# System info
neofetch
```

### Process Management
```bash
# Find Python processes
ps aux | grep python

# Kill specific process
kill -9 <PID>

# Kill all Python processes (careful!)
pkill -f python
```

---

## 🔧 Maintenance

### Update Application
```bash
cd ~/auto-print

# Pull latest changes (if using git)
git pull

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart service
sudo systemctl restart auto-print
```

### Update System
```bash
# Update package list
sudo apt update

# Upgrade packages
sudo apt upgrade -y

# Full upgrade (including kernel)
sudo apt full-upgrade -y

# Clean up
sudo apt autoremove -y
sudo apt autoclean
```

### Backup
```bash
# Backup entire project
tar -czf auto-print-backup-$(date +%Y%m%d).tar.gz ~/auto-print

# Backup only configuration
cp ~/auto-print/serviceAccountKey.json ~/backups/
cp ~/auto-print/main.py ~/backups/
```

---

## 🌐 Network

### Check Network Status
```bash
# IP address
hostname -I

# Network interfaces
ip addr show

# WiFi status
iwconfig

# Test connectivity
ping -c 4 google.com

# Check if backend is reachable
curl http://your-backend-ip:5000
```

### Configure WiFi
```bash
# Edit WiFi configuration
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Restart networking
sudo systemctl restart networking

# Or use raspi-config
sudo raspi-config
# Navigate to: System Options > Wireless LAN
```

---

## 🔒 Security

### Firewall (UFW)
```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow specific port
sudo ufw allow 5000

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### User Management
```bash
# Change password
passwd

# Add new user
sudo adduser username

# Add user to groups
sudo usermod -a -G lpadmin,sudo username
```

### File Permissions
```bash
# Secure Firebase key
chmod 600 ~/auto-print/serviceAccountKey.json

# Make script executable
chmod +x ~/auto-print/setup_pi.sh

# Check permissions
ls -la ~/auto-print/
```

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status auto-print

# View detailed logs
sudo journalctl -u auto-print.service -n 100 --no-pager

# Test manually
cd ~/auto-print
source venv/bin/activate
python main.py
```

### Printer Not Working
```bash
# Check USB devices
lsusb

# Check CUPS error log
sudo tail -f /var/log/cups/error_log

# Restart CUPS
sudo systemctl restart cups

# Re-add printer via web interface
# http://localhost:631
```

### Python Module Errors
```bash
# Reinstall all dependencies
cd ~/auto-print
source venv/bin/activate
pip install --upgrade pip
pip install --force-reinstall -r requirements.txt
```

### Out of Disk Space
```bash
# Check disk usage
df -h

# Find large files
sudo du -h / | sort -rh | head -20

# Clean up
sudo apt autoremove -y
sudo apt autoclean
rm -rf ~/auto-print/temp_jobs/*
```

---

## ⚡ Performance

### Optimize Raspberry Pi
```bash
# Increase swap size (if needed)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Check memory usage
free -h

# Reduce GPU memory (headless setup)
sudo raspi-config
# Navigate to: Performance Options > GPU Memory > Set to 16
```

---

## 📱 Remote Access

### SSH
```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Connect from another machine
ssh pi@<raspberry-pi-ip>

# Copy files to Pi
scp file.txt pi@<raspberry-pi-ip>:~/auto-print/
```

### VNC (Desktop Only)
```bash
# Enable VNC
sudo raspi-config
# Navigate to: Interface Options > VNC > Enable

# Connect using VNC Viewer
# Address: <raspberry-pi-ip>:5900
```

---

## 🔄 Reboot & Shutdown

```bash
# Reboot
sudo reboot

# Shutdown
sudo shutdown -h now

# Shutdown in 10 minutes
sudo shutdown -h +10

# Cancel shutdown
sudo shutdown -c
```

---

## 📝 Useful Aliases

Add these to `~/.bashrc` for quick access:

```bash
# Edit .bashrc
nano ~/.bashrc

# Add these lines:
alias autoprint='cd ~/auto-print && source venv/bin/activate'
alias printlog='sudo journalctl -u auto-print.service -f'
alias printstatus='sudo systemctl status auto-print'
alias printrestart='sudo systemctl restart auto-print'

# Reload .bashrc
source ~/.bashrc
```

---

## 🆘 Emergency Recovery

### Safe Mode Boot
1. Power off Raspberry Pi
2. Edit `config.txt` on boot partition
3. Add: `init=/bin/sh`
4. Boot and fix issues
5. Remove the line and reboot

### Reinstall Application
```bash
# Backup configuration
cp ~/auto-print/serviceAccountKey.json ~/
cp ~/auto-print/main.py ~/main.py.backup

# Remove and reinstall
rm -rf ~/auto-print
git clone <your-repo> ~/auto-print
cd ~/auto-print

# Restore configuration
cp ~/serviceAccountKey.json ~/auto-print/
# Edit main.py with your settings

# Run setup
chmod +x setup_pi.sh
./setup_pi.sh
```

---

## 📚 Additional Resources

- **Raspberry Pi Documentation**: https://www.raspberrypi.org/documentation/
- **CUPS Documentation**: https://www.cups.org/doc/
- **systemd Manual**: `man systemd.service`
- **Python venv**: https://docs.python.org/3/library/venv.html
