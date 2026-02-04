import threading
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Fallback for testing on Windows
    GPIO = None

class GPIOKeypadReader:
    def __init__(self, callback=None):
        self.callback = callback
        self.running = False
        self._thread = None
        
        # Mapping as requested (B->1, C->2, D->3)
        self.KEY_MAP = [
            ["1", "2", "3", "A"],
            ["4", "5", "6", "1"], # B -> 1
            ["7", "8", "9", "2"], # C -> 2
            ["*", "0", "#", "3"]  # D -> 3
        ]
        
        # BCM Pin numbers
        self.ROW_PINS = [5, 6, 13, 19]
        self.COL_PINS = [26, 21, 20, 16]

    def start(self):
        if GPIO is None:
            print("❌ GPIO library not found. GPIO Keypad Reader cannot start.")
            return False
            
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup pins
        for pin in self.ROW_PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
            
        for pin in self.COL_PINS:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        self.running = True
        self._thread = threading.Thread(target=self._scan, daemon=True)
        self._thread.start()
        print("⌨️  GPIO Keypad Reader started directly on Raspberry Pi pins")
        return True

    def _scan(self):
        last_pressed = None
        while self.running:
            key_detected = None
            
            for r_idx, r_pin in enumerate(self.ROW_PINS):
                GPIO.output(r_pin, GPIO.LOW)
                for c_idx, c_pin in enumerate(self.COL_PINS):
                    if GPIO.input(c_pin) == GPIO.LOW:
                        key_detected = self.KEY_MAP[r_idx][c_idx]
                GPIO.output(r_pin, GPIO.HIGH)
                
            if key_detected != last_pressed:
                if key_detected:
                    # Map special buttons for the UI
                    final_val = key_detected
                    if key_detected == "#": final_val = "CLEAR"
                    if key_detected == "*": final_val = "BACKSPACE"
                    
                    if self.callback:
                        self.callback(final_val)
                last_pressed = key_detected
                
            time.sleep(0.1) # Debounce/Polling delay

    def stop(self):
        self.running = False
        if GPIO:
            GPIO.cleanup()
