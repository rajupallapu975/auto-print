# 📟 Auto-Print Kiosk System (Raspberry Pi + Arduino)

This folder contains the complete professional setup for an automated printing kiosk.

## 📁 System Architecture

```
auto-print/
├── arduino/
│   └── keypad_sender.ino    # Code for Arduino Uno (reads 4x4 keypad)
├── hardware/
│   └── serial_reader.py     # Python module to listen to Arduino via USB
├── gui/
│   └── app_interface.py     # Kiosk UI (Fullscreen, real-time feedback)
├── services/
│   ├── firebase_service.py  # Firestore lookups
│   ├── backend_service.py   # File downloads
│   └── printer_service.py   # CUPS / Local Print logic
└── main.py                  # System Orchestrator
```

## 🔌 Hardware Setup

### 1. Keypad to Arduino
Connect your 4x4 Matrix Keypad to the Arduino Uno:
- **Row Pins (1-4)**: Arduino Pins 9, 8, 7, 6
- **Col Pins (1-4)**: Arduino Pins 5, 4, 3, 2

### 2. Arduino to Raspberry Pi
- Connect the Arduino Uno to any USB port on the Raspberry Pi 4.

## 🚀 Installation & Launch

### 1. Prepare Arduino
1. Open `arduino/keypad_sender.ino` in Arduino IDE.
2. Install the "Keypad" library.
3. Upload to your Uno.

### 2. Prepare Raspberry Pi
1. Run the setup script:
   ```bash
   ./setup_pi.sh
   ```
2. Install the serial dependency:
   ```bash
   pip install pyserial
   ```

### 3. Run the Kiosk
```bash
python3 main.py
```

## ✨ User Interaction Flow

1. **Idle State**: The screen shows "Please enter your 6-digit Pickup Code".
2. **Numeric Input**: As the user types on the **physical keypad**, the numbers appear on the **screen interface** in real-time.
3. **Auto-Verification**: Once the 6th digit is pressed, the system automatically:
   - Displays "Verifying code..."
   - Checks Firestore for the order.
4. **Processing**:
   - **Incorrect Code**: Shows "❌ No matching files found" on the interface for 3 seconds, then resets.
   - **Correct Code**: Shows "✅ VERIFIED" → "Preparing files..." → "Printing file X of Y...".
5. **Completion**: Screen shows "Printing Complete!" then resets for the next customer.

## 🛠️ Efficient Configuration
- **fullscreen**: Set in `gui/app_interface.py` (Default: True). Press `Esc` to minimize.
- **serial port**: Automatically detected in `hardware/serial_reader.py`.
- **timeout**: Verification messages stay on screen for fixed durations for better UX.

---
**Maintained by Antigravity AI**
