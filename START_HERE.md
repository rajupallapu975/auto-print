# 🍓 Raspberry Pi 4 - Getting Started

**Quick guide to get your Auto-Print Module running on Raspberry Pi 4**

---

## 📚 Documentation Overview

Your project now includes comprehensive Raspberry Pi support with the following guides:

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **README.md** | Project overview and quick start | First read, general reference |
| **RASPBERRY_PI_SETUP.md** | Complete setup guide | Full deployment instructions |
| **DEPLOYMENT_CHECKLIST.md** | Step-by-step checklist | During deployment |
| **PI_QUICK_REFERENCE.md** | Command reference | Daily operations |
| **KEYPAD_GUI_README.md** | GUI interface guide | Using with display/touchscreen |
| **START_HERE.md** | This file | Getting started |

---

## 🚀 Quick Start (3 Steps)

### Step 1: Transfer Files to Raspberry Pi

**From Windows (PowerShell):**
```powershell
cd d:\psfc\auto-print
.\transfer_to_pi.ps1 -PiIP <your-pi-ip-address>
```

**Or manually via SCP:**
```powershell
scp -r d:\psfc\auto-print pi@<pi-ip>:~/auto-print
```

### Step 2: Run Setup Script on Pi

**SSH into your Raspberry Pi:**
```bash
ssh pi@<pi-ip>
```

**Run the automated setup:**
```bash
cd ~/auto-print
chmod +x setup_pi.sh
./setup_pi.sh
```

This will:
- Update system packages
- Install CUPS and Python dependencies
- Setup virtual environment
- Configure printer permissions

### Step 3: Configure and Run

**Edit configuration:**
```bash
nano ~/auto-print/main.py
```

Update these values:
```python
BACKEND_BASE_URL = "http://your-backend-ip:5000"  # Your backend server
PRINTER_NAME = None  # Or your printer name from: lpstat -p -d
```

**Run the application:**
```bash
source venv/bin/activate
python main.py
```

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Raspberry Pi 4** with Raspberry Pi OS installed
- [ ] **USB Printer** connected to the Pi
- [ ] **Network connection** (WiFi or Ethernet)
- [ ] **Firebase credentials** (`serviceAccountKey.json`)
- [ ] **Backend server** running and accessible
- [ ] **SSH access** to your Raspberry Pi

---

## 🔧 What's Different on Raspberry Pi?

### Windows (Development)
- Uses `SmartPrinter` for testing
- Simulates print jobs
- Good for development

### Raspberry Pi (Production)
- Uses `RealPrinter` via CUPS
- Actually prints documents
- Production-ready

### Key Changes Needed
1. **Backend URL**: Change from `localhost` to actual server IP
2. **Printer Setup**: Configure physical printer via CUPS
3. **Auto-start**: Optional systemd service for boot startup

---

## 🖨️ Printer Setup

### 1. Connect Printer
- Plug USB printer into Raspberry Pi
- Power on the printer

### 2. Verify Detection
```bash
lsusb  # Should show your printer
```

### 3. Add Printer via CUPS
Open browser to: `http://<pi-ip>:631`
- Go to: Administration → Add Printer
- Select your USB printer
- Follow the wizard

### 4. Test Print
```bash
lpstat -p -d  # Get printer name
lp -d <printer-name> /usr/share/cups/data/testprint
```

---

## 🔄 Typical Workflow

### Initial Setup (One Time)
1. Transfer files to Pi
2. Run `setup_pi.sh`
3. Configure `main.py`
4. Setup printer in CUPS
5. Test the application

### Daily Operation

**Option 1: Terminal Mode (SSH/Headless)**
```bash
# Start application
cd ~/auto-print
source venv/bin/activate
python main.py

# Or if using systemd service:
sudo systemctl start auto-print
```

**Option 2: GUI Mode (With Display/Touchscreen)**
```bash
# Start keypad GUI
cd ~/auto-print
source venv/bin/activate
python keypad_gui.py

# Or use the launcher:
./start_keypad_gui.sh
```

> **💡 Tip**: Use GUI mode when you have a display connected to the Pi. Use terminal mode for headless/SSH operation.

### Maintenance
```bash
# View logs
sudo journalctl -u auto-print -f

# Update code
cd ~/auto-print
git pull
pip install -r requirements.txt

# Restart service
sudo systemctl restart auto-print
```

---

## 🆘 Common Issues & Solutions

### "Printer not found"
```bash
# Check CUPS status
sudo systemctl status cups

# List printers
lpstat -p -d

# Restart CUPS
sudo systemctl restart cups
```

### "Cannot connect to backend"
```bash
# Test connectivity
ping <backend-ip>
curl http://<backend-ip>:5000

# Check firewall
sudo ufw status
```

### "Module not found" errors
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### "Permission denied" for printer
```bash
# Add user to lpadmin group
sudo usermod -a -G lpadmin $USER

# Reboot to apply
sudo reboot
```

---

## 🎯 Recommended Reading Order

1. **START_HERE.md** (this file) - Overview and quick start
2. **DEPLOYMENT_CHECKLIST.md** - Follow during setup
3. **RASPBERRY_PI_SETUP.md** - Detailed instructions
4. **PI_QUICK_REFERENCE.md** - Bookmark for daily use

---

## 💡 Pro Tips

### Auto-Start on Boot
```bash
# Copy service file
sudo cp auto-print.service /etc/systemd/system/

# Enable service
sudo systemctl enable auto-print
sudo systemctl start auto-print
```

### Remote Monitoring
```bash
# View logs remotely
ssh pi@<pi-ip> "sudo journalctl -u auto-print -f"

# Check status remotely
ssh pi@<pi-ip> "sudo systemctl status auto-print"
```

### Backup Configuration
```bash
# Backup important files
tar -czf backup.tar.gz serviceAccountKey.json main.py
scp backup.tar.gz user@backup-server:~/backups/
```

---

## 📞 Need Help?

### Check These First
1. Service status: `sudo systemctl status auto-print`
2. Recent logs: `sudo journalctl -u auto-print -n 50`
3. Printer status: `lpstat -p -d`
4. Network: `ping <backend-ip>`

### Documentation
- **Detailed setup**: See `RASPBERRY_PI_SETUP.md`
- **Commands**: See `PI_QUICK_REFERENCE.md`
- **Troubleshooting**: See `RASPBERRY_PI_SETUP.md` → Troubleshooting section

---

## 🎉 You're Ready!

Follow the **Quick Start** section above to get started, or use the **DEPLOYMENT_CHECKLIST.md** for a guided setup process.

**Happy Printing! 🖨️**
