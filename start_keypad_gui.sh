#!/bin/bash

# Auto-Print Keypad GUI Launcher
# This script launches the GUI interface for entering pickup codes

echo "🚀 Starting Auto-Print Keypad GUI..."
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the GUI
python3 keypad_gui.py
