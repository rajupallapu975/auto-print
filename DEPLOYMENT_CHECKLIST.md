# ✅ Raspberry Pi Deployment Checklist

Use this checklist to ensure a smooth deployment of the Auto-Print Module on your Raspberry Pi 4.

---

## 📦 Pre-Deployment (On Your Computer)

- [ ] **Download Firebase credentials**
  - Go to Firebase Console → Project Settings → Service Accounts
  - Click "Generate new private key"
  - Save as `serviceAccountKey.json`

- [ ] **Note your backend server details**
  - Backend server IP address or domain: `________________`
  - Backend server port (default 5000): `________________`

- [ ] **Prepare Raspberry Pi**
  - Flash Raspberry Pi OS to microSD card
  - Enable SSH (create empty `ssh` file in boot partition)
  - Configure WiFi (optional: create `wpa_supplicant.conf`)

---

## 🍓 Initial Raspberry Pi Setup

- [ ] **Boot and connect**
  - Insert microSD card and power on
  - Find Pi's IP address (check router or use `ping raspberrypi.local`)
  - SSH into Pi: `ssh pi@<ip-address>` (default password: `raspberry`)

- [ ] **Change default password**
  ```bash
  passwd
  ```

- [ ] **Update system**
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```

- [ ] **Set timezone and locale**
  ```bash
  sudo raspi-config
  # Navigate to: Localisation Options
  ```

---

## 📁 Transfer Project Files

Choose one method:

### Option A: Git Clone
- [ ] Clone repository
  ```bash
  cd ~
  git clone <your-repo-url> auto-print
  cd auto-print
  ```

### Option B: SCP Transfer
- [ ] Transfer from Windows
  ```powershell
  # On Windows PowerShell
  scp -r d:\psfc\auto-print pi@<pi-ip>:~/auto-print
  ```

### Option C: USB Drive
- [ ] Copy files from USB
  ```bash
  cp -r /media/usb/auto-print ~/auto-print
  cd ~/auto-print
  ```

---

## 🔧 Installation

- [ ] **Run setup script**
  ```bash
  cd ~/auto-print
  chmod +x setup_pi.sh
  ./setup_pi.sh
  ```

  OR manually:

- [ ] **Install system dependencies**
  ```bash
  sudo apt install -y python3-pip python3-venv cups cups-client
  ```

- [ ] **Setup Python environment**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- [ ] **Configure CUPS**
  ```bash
  sudo systemctl enable cups
  sudo systemctl start cups
  sudo usermod -a -G lpadmin $USER
  ```

---

## 🔑 Configuration

- [ ] **Transfer Firebase credentials**
  ```bash
  # Using scp from Windows:
  scp d:\psfc\auto-print\serviceAccountKey.json pi@<pi-ip>:~/auto-print/
  ```

- [ ] **Verify Firebase key exists**
  ```bash
  ls -la ~/auto-print/serviceAccountKey.json
  chmod 600 ~/auto-print/serviceAccountKey.json
  ```

- [ ] **Configure backend URL**
  ```bash
  nano ~/auto-print/main.py
  ```
  Update `BACKEND_BASE_URL` to your server address

- [ ] **Test backend connectivity**
  ```bash
  curl http://<your-backend-ip>:5000
  ```

---

## 🖨️ Printer Setup

- [ ] **Connect USB printer to Raspberry Pi**

- [ ] **Verify printer is detected**
  ```bash
  lsusb
  ```

- [ ] **Add printer via CUPS**
  - Open browser to: `http://<pi-ip>:631`
  - Go to: Administration → Add Printer
  - Follow wizard to add your printer

- [ ] **Check printer status**
  ```bash
  lpstat -p -d
  ```

- [ ] **Print test page**
  ```bash
  lp -d <printer-name> /usr/share/cups/data/testprint
  ```

- [ ] **Update printer name in code (if needed)**
  ```bash
  nano ~/auto-print/main.py
  # Set PRINTER_NAME = "YourPrinterName"
  ```

---

## 🧪 Testing

- [ ] **Test application manually**
  ```bash
  cd ~/auto-print
  source venv/bin/activate
  python main.py
  ```

- [ ] **Enter a test pickup code**
  - Verify Firestore connection
  - Verify file download
  - Verify print job submission

- [ ] **Check for errors**
  - Review console output
  - Check printer queue: `lpq`

---

## 🚀 Production Setup

- [ ] **Install systemd service**
  ```bash
  sudo cp ~/auto-print/auto-print.service /etc/systemd/system/
  sudo nano /etc/systemd/system/auto-print.service
  # Update paths if your username isn't 'pi'
  ```

- [ ] **Enable and start service**
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable auto-print
  sudo systemctl start auto-print
  ```

- [ ] **Verify service is running**
  ```bash
  sudo systemctl status auto-print
  ```

- [ ] **Check logs**
  ```bash
  sudo journalctl -u auto-print -f
  ```

---

## 🔒 Security Hardening

- [ ] **Change default password** (if not done already)
  ```bash
  passwd
  ```

- [ ] **Setup firewall**
  ```bash
  sudo apt install ufw
  sudo ufw allow ssh
  sudo ufw enable
  ```

- [ ] **Disable unnecessary services**
  ```bash
  sudo systemctl disable bluetooth
  # Add others as needed
  ```

- [ ] **Keep system updated**
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```

- [ ] **Secure Firebase key**
  ```bash
  chmod 600 ~/auto-print/serviceAccountKey.json
  ```

---

## 📊 Monitoring Setup

- [ ] **Create logs directory**
  ```bash
  mkdir -p ~/auto-print/logs
  ```

- [ ] **Setup log rotation** (optional)
  ```bash
  sudo nano /etc/logrotate.d/auto-print
  ```

- [ ] **Test monitoring commands**
  ```bash
  # System status
  sudo systemctl status auto-print
  
  # Live logs
  sudo journalctl -u auto-print -f
  
  # Temperature
  vcgencmd measure_temp
  ```

---

## 🔄 Post-Deployment

- [ ] **Reboot and verify auto-start**
  ```bash
  sudo reboot
  ```
  Wait for reboot, then:
  ```bash
  sudo systemctl status auto-print
  ```

- [ ] **Test end-to-end workflow**
  - Create test order in your app
  - Verify pickup code works
  - Verify files download
  - Verify printing works

- [ ] **Document your setup**
  - Note printer name: `________________`
  - Note backend URL: `________________`
  - Note Pi IP address: `________________`

---

## 📝 Maintenance Schedule

- [ ] **Daily**: Check service status
  ```bash
  sudo systemctl status auto-print
  ```

- [ ] **Weekly**: Review logs
  ```bash
  sudo journalctl -u auto-print --since "1 week ago"
  ```

- [ ] **Monthly**: Update system
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```

- [ ] **As needed**: Clear temp files
  ```bash
  rm -rf ~/auto-print/temp_jobs/*
  ```

---

## 🆘 Troubleshooting Reference

If issues occur, check:

1. **Service status**: `sudo systemctl status auto-print`
2. **Logs**: `sudo journalctl -u auto-print -n 50`
3. **Printer**: `lpstat -p -d`
4. **Network**: `ping <backend-ip>`
5. **Disk space**: `df -h`
6. **Temperature**: `vcgencmd measure_temp`

See `PI_QUICK_REFERENCE.md` for detailed troubleshooting commands.

---

## ✅ Deployment Complete!

Once all items are checked, your Raspberry Pi Auto-Print Module is ready for production use!

**Quick access commands:**
```bash
# View status
sudo systemctl status auto-print

# View logs
sudo journalctl -u auto-print -f

# Restart service
sudo systemctl restart auto-print

# Manual run
cd ~/auto-print && source venv/bin/activate && python main.py
```

---

## 📚 Documentation Reference

- **Setup Guide**: `RASPBERRY_PI_SETUP.md`
- **Quick Reference**: `PI_QUICK_REFERENCE.md`
- **Main README**: `README.md`
