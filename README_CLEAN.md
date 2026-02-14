# Auto-Print System

**Streamlined Raspberry Pi Auto-Print Module**

## 📁 Project Structure

```
auto-print/
├── config.py                 # Centralized configuration
├── main_v2.py               # Main application (use this)
├── services/                # Backend services
│   ├── backend_service.py   # API communication
│   ├── smart_printer.py     # Printer management
│   └── firebase_service.py  # Firebase (optional)
├── hardware/                # Hardware interfaces
│   └── serial_reader.py     # Arduino keypad
├── gui/                     # User interface
│   └── app_interface.py     # Display UI
└── arduino/                 # Arduino sketch
    └── keypad_sender.ino    # Keypad firmware
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure
Edit `config.py` to set your backend URL and printer settings.

### 3. Run
```bash
python main_v2.py
```

## 📋 Features

- ✅ Keypad input (Arduino)
- ✅ Backend verification
- ✅ Cloudinary file download
- ✅ Automatic printing
- ✅ Error handling
- ✅ Status tracking

## 🔧 Configuration

All settings are in `config.py`:
- Backend URL
- Printer name
- Arduino port
- Retry settings

## 📝 Workflow

1. User enters pickup code
2. System verifies with backend
3. Downloads files from Cloudinary
4. Checks printer availability
5. Prints files
6. Marks order as complete

## 🐛 Debugging

Check logs in `autoprint.log`

Test Firebase connection:
```bash
python debug_order.py <pickup_code>
```

## 📦 Deployment

See `RASPBERRY_PI_SETUP.md` for full deployment instructions.

## 🔐 Security

- Keep `serviceAccountKey.json` secure
- Use environment variables for production
