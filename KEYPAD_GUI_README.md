# 🖨️ Auto-Print Keypad GUI

A graphical user interface with a numeric keypad for entering pickup codes on the Raspberry Pi.

## 🎯 Purpose

This GUI replaces the terminal-based input system, allowing users to enter pickup codes using an on-screen numeric keypad instead of typing in the terminal.

## ✨ Features

- **Numeric Keypad**: Large, touch-friendly buttons (0-9)
- **Visual Feedback**: Real-time display of entered code
- **Control Buttons**:
  - ✓ **SUBMIT**: Process the pickup code and print
  - **C**: Clear entire code
  - **⌫**: Backspace (delete last digit)
  - ✕ **EXIT**: Close the application
- **Status Indicators**: Shows printer status and processing updates
- **Background Processing**: Non-blocking UI during print jobs
- **Error Handling**: User-friendly error messages

## 🚀 How to Use

### On Raspberry Pi (with Display)

1. **Make the launcher executable** (first time only):
   ```bash
   chmod +x start_keypad_gui.sh
   ```

2. **Launch the GUI**:
   ```bash
   ./start_keypad_gui.sh
   ```

   Or directly:
   ```bash
   python3 keypad_gui.py
   ```

3. **Enter Pickup Code**:
   - Click the number buttons to enter the code
   - Use **⌫** to delete mistakes
   - Use **C** to clear and start over
   - Click **✓ SUBMIT** when ready

4. **Wait for Processing**:
   - The system will fetch the order from Firestore
   - Download files from the backend
   - Send to the printer
   - Show success/error message

## 🖥️ Display Requirements

- **Recommended**: 7" touchscreen or larger
- **Minimum Resolution**: 480x600 pixels
- **Input**: Mouse, touchscreen, or keyboard

## 🎨 Interface Layout

```
┌─────────────────────────────────────┐
│      🖨️ Auto-Print System          │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐  │
│  │   Enter Pickup Code           │  │
│  │   (or entered digits)         │  │
│  └───────────────────────────────┘  │
├─────────────────────────────────────┤
│         ┌───┬───┬───┐               │
│         │ 1 │ 2 │ 3 │               │
│         ├───┼───┼───┤               │
│         │ 4 │ 5 │ 6 │               │
│         ├───┼───┼───┤               │
│         │ 7 │ 8 │ 9 │               │
│         ├───┼───┼───┤               │
│         │ C │ 0 │ ⌫ │               │
│         └───┴───┴───┘               │
├─────────────────────────────────────┤
│   ┌─────────┐   ┌─────────┐        │
│   │✓ SUBMIT │   │✕ EXIT   │        │
│   └─────────┘   └─────────┘        │
├─────────────────────────────────────┤
│         Status: Ready               │
└─────────────────────────────────────┘
```

## 🔧 Configuration

Edit `keypad_gui.py` to change:

```python
# Backend URL (line 17)
self.BACKEND_BASE_URL = "http://localhost:5000"

# Printer name (line 18)
self.PRINTER_NAME = None  # or "HP_LaserJet_Pro"

# Window size (line 13)
self.root.geometry("480x600")
```

## 🎯 Auto-Start on Boot (Optional)

To launch the GUI automatically when Raspberry Pi boots:

1. **Create desktop autostart entry**:
   ```bash
   mkdir -p ~/.config/autostart
   nano ~/.config/autostart/auto-print-gui.desktop
   ```

2. **Add this content**:
   ```ini
   [Desktop Entry]
   Type=Application
   Name=Auto-Print Keypad
   Exec=/home/pi/auto-print/start_keypad_gui.sh
   Terminal=false
   ```

3. **Save and reboot**

## 🐛 Troubleshooting

### GUI doesn't appear
- Check if X server is running: `echo $DISPLAY`
- Try: `export DISPLAY=:0` then run again

### Buttons not responding
- Check if tkinter is installed: `python3 -m tkinter`
- Install if needed: `sudo apt-get install python3-tk`

### Printer not found
- Verify printer is connected: `lpstat -p -d`
- Check printer name in configuration

## 📝 Comparison: GUI vs Terminal

| Feature | Terminal (`main.py`) | GUI (`keypad_gui.py`) |
|---------|---------------------|----------------------|
| Input Method | Keyboard typing | On-screen keypad |
| Visual Feedback | Text only | Graphical display |
| User Experience | Technical | User-friendly |
| Touch Support | No | Yes |
| Best For | Headless/SSH | Display connected |

## 🔄 Switching Between Modes

- **Use GUI**: When Raspberry Pi has a display connected
- **Use Terminal**: When accessing via SSH or headless setup

Both use the same backend services and printing logic!

## 📦 Dependencies

Same as `main.py`:
- `firebase_service.py`
- `backend_service.py`
- `smart_printer.py`
- Python 3.7+
- tkinter (usually pre-installed)

## 🎨 Color Scheme

- **Background**: Dark blue (#1a1a2e)
- **Accent**: Cyan (#00d4ff)
- **Numbers**: Bright cyan buttons
- **Clear**: Red (#e74c3c)
- **Backspace**: Orange (#f39c12)
- **Submit**: Green (#27ae60)
- **Exit**: Gray (#95a5a6)

---

**Made with ❤️ for easy pickup code entry!**
