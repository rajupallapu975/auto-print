import serial
import serial.tools.list_ports
import threading
import time
import sys

class ArduinoSerialReader:
    def __init__(self, port=None, baudrate=9600, callback=None):
        self.port = port # Manually specified port (e.g. 'COM19')
        self.baudrate = baudrate
        self.callback = callback # Function to call when a key is received
        self.ser = None
        self.running = False
        self._thread = None

    def find_arduino_port(self):
        """Attempts to find the Arduino port automatically on Windows and Linux."""
        ports = list(serial.tools.list_ports.comports())
        
        # 1. Look for specific Arduino keywords
        for port in ports:
            if "Arduino" in port.description or "ttyACM" in port.device or "ttyUSB" in port.device:
                return port.device
        
        # 2. On Windows, if we only have one port, it's likely the Arduino
        if sys.platform.startswith('win'):
            if len(ports) > 0:
                # Use the last (highest index) COM port which is usually the one most recently plugged in
                return ports[-1].device
            return "COM3" # Fallback common on Windows
            
        return "/dev/ttyACM0" # Fallback for Raspberry Pi

    def start(self):
        """Starts the background thread to listen to Serial."""
        port = self.port if self.port else self.find_arduino_port()
        try:
            self.ser = serial.Serial(port, self.baudrate, timeout=1)
            self.running = True
            self._thread = threading.Thread(target=self._listen, daemon=True)
            self._thread.start()
            print(f"📡 Serial Reader started on {port}")
            return True
        except Exception as e:
            print(f"❌ Could not start Serial Reader: {e}")
            return False

    def _listen(self):
        """Internal loop to read serial data."""
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    if line and self.callback:
                        self.callback(line)
                time.sleep(0.01) # Low latency check
            except Exception as e:
                print(f"⚠️ Serial read error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()
