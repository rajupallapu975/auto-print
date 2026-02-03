<<<<<<< HEAD
# 🖨️ Raspberry Pi Auto-Print Module

Automated print job processing system that fetches orders from Firestore and prints them using CUPS on Linux/Raspberry Pi.

---

## 🚀 Quick Start

### For Windows (Development/Testing)
1. **Setup Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. **Install & Run**:
   ```powershell
   pip install -r requirements.txt
   python main.py
   ```

### For Raspberry Pi 4 (Production)

**📖 See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for complete deployment guide**

Quick setup:
```bash
# 1. Install system dependencies
sudo apt update && sudo apt install -y python3-pip python3-venv cups

# 2. Setup project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure and run
python main.py
```

---

## 🔑 Prerequisites

### Required Files
- **`serviceAccountKey.json`**: Firebase Admin SDK credentials
  - Download from: Firebase Console → Project Settings → Service Accounts
  - Place in project root directory
  - ⚠️ **Critical**: The placeholder file won't work!

### System Requirements
- **Python 3.7+**
- **CUPS** (Linux/macOS) for actual printing
- **Network access** to backend server and Firebase

---

## 📂 Project Structure

```
auto-print/
├── main.py                    # Main entry point
├── firebase_service.py        # Firestore order lookup
├── backend_service.py         # File download from backend
├── smart_printer.py           # Cross-platform printer (Windows/Linux)
├── real_printer.py            # Linux CUPS printer
├── fake_printer.py            # Testing/simulation printer
├── requirements.txt           # Python dependencies
├── serviceAccountKey.json     # Firebase credentials (YOU MUST ADD THIS)
├── temp_jobs/                 # Downloaded files storage
├── README.md                  # This file
└── RASPBERRY_PI_SETUP.md      # Complete Pi deployment guide
```

---

## ⚙️ Configuration

Edit `main.py` to configure:

```python
# Backend server URL
BACKEND_BASE_URL = "http://your-server-ip:5000"

# Printer name (or None for default)
PRINTER_NAME = None  # Find with: lpstat -p -d
```

---

## 🖨️ Printer Support

| Platform | Printer Class | Status |
|----------|---------------|--------|
| **Linux/Raspberry Pi** | `SmartPrinter` / `RealPrinter` | ✅ Production Ready |
| **Windows** | `SmartPrinter` | ✅ Testing Only |
| **Testing** | `FakePrinter` | ✅ Simulation |

---

## 🔧 Usage

1. **Start the application**:
   ```bash
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\Activate.ps1  # Windows
   
   python main.py
   ```

2. **Enter pickup code** when prompted

3. **System will**:
   - Fetch order from Firestore
   - Download files from backend
   - Print with specified settings

---

## 🐛 Troubleshooting

### Printer Not Found
```bash
# Check available printers
lpstat -p -d

# Check CUPS status
sudo systemctl status cups
```

### Module Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Backend Connection Failed
- Verify `BACKEND_BASE_URL` in `main.py`
- Check network connectivity
- Ensure backend server is running

---

## 📚 Documentation

- **[RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)** - Complete Raspberry Pi deployment guide
  - Hardware setup
  - CUPS configuration
  - Auto-start on boot
  - Troubleshooting
  - Security best practices

---

## 🔒 Security Notes

- Keep `serviceAccountKey.json` secure (never commit to git)
- Use firewall rules on Raspberry Pi
- Change default passwords
- Keep system packages updated

---

## 📝 License

[Your License Here]
=======
# auto-print
>>>>>>> 2e397e4aa2d5968f6bc47b86e477a589f0dd91d0
