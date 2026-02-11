import tkinter as tk
import sys
import os

# Add the current directory to path for imports to work across folders
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hardware.serial_reader import ArduinoSerialReader
from gui.app_interface import AutoPrintUI
# from services.firebase_service import FirebaseService
from services.backend_service import BackendService
from services.smart_printer import SmartPrinter

class AutoPrintMain:
    def __init__(self):
        self.root = tk.Tk()
        
        # self.fb_service = FirebaseService() # Removed for Supabase/Backend migration
        
        # 🔗 Backend API URL
        # IMPORTANT: Change 'localhost' to your Laptop's IP (e.g., "http://192.168.1.10:5000")
        # when running on the Raspberry Pi!
        LAPTOP_IP = "10.71.181.155" 
        self.backend = BackendService(base_url=f"https://printer-backend-ch2e.onrender.com")
        self.printer = SmartPrinter(printer_name=None)
        
        # Initialize GUI
        self.ui = AutoPrintUI(self.root, on_code_complete=self.process_verification)
        
        # Initialize Hardware Input: Always use Serial (Arduino)
        # On Windows, we specify COM19. On Linux/Pi, it auto-detects (e.g. /dev/ttyACM0)
        arduino_port = "COM19" if sys.platform.startswith('win') else None
        self.reader = ArduinoSerialReader(port=arduino_port, callback=self.handle_keypad_input)

    def handle_keypad_input(self, char):
        """Bridge between Hardware and GUI. Maps letters to numbers if needed."""
        print(f"⌨️ Keypad received: {char}")
        
        # Mapping Logic
        mapping = {
            'B': '1',
            'C': '2',
            'D': '3',
            'A': '0'  # You can change A to whatever you want
        }
        
        # If the character is one of our special letters, convert it
        final_char = mapping.get(char, char)
        
        # Use root.after to safely update the UI from the serial thread
        self.root.after(0, self.ui.handle_key_input, final_char)

    def process_verification(self, code):
        """The core logic that runs when 6 digits are entered."""
        try:
            # 1. Ask Backend to verify in Firebase (Cloudinary Flow)
            verify_res = self.backend.verify_code(code)
            
            if not verify_res.get("success"):
                error_msg = verify_res.get("error", "Invalid code")
                if error_msg == "IP_ERROR":
                    self.root.after(0, self.ui.show_error, "Backend IP Error: Check Connection")
                else:
                    self.root.after(0, self.ui.show_error, "Invalid or Expired Code")
                return

            order_id = verify_res.get("orderId")
            
            # 2. Download files using URLs from Backend
            self.root.after(0, self.ui.show_success, "Code Verified! Preparing files...")
            downloaded_items = self.backend.download_files(verify_res)
            
            if not downloaded_items:
                self.root.after(0, self.ui.show_error, "Error downloading files")
                return

            # 3. Print Files
            print_settings = verify_res.get('printSettings', {})
            global_duplex = print_settings.get('doubleSide', False)
            total_files = len(downloaded_items)

            for i, item in enumerate(downloaded_items):
                # Update UI status
                self.root.after(0, self.ui.update_printing_status, i+1, total_files)
                
                final_settings = {
                    "copies": item.get('settings', {}).get('copies', 1),
                    "color": item.get('settings', {}).get('color', 'BW'),
                    "duplex": global_duplex,
                    "orientation": item.get('settings', {}).get('orientation', 'PORTRAIT'),
                }
                
                # Perform the print
                self.printer.print_job([item], final_settings)
            
            # 4. Notify Backend to Revoke Code in Firebase
            self.backend.mark_as_printed(order_id)

            self.root.after(0, self.ui.show_success, "Printing Complete!")
            time_to_wait = 5000 # 5 seconds
            self.root.after(time_to_wait, self.ui.reset_ui, "Ready for next customer")

        except Exception as e:
            print(f"❌ Main Process Error: {e}")
            self.root.after(0, self.ui.show_error, f"System Error: {str(e)}")

    def run(self):
        # Start hardware listener
        if self.reader.start():
            print("🚀 System Online. Waiting for input...")
            self.root.mainloop()
        else:
            print("❌ Failed to start serial reader. Is Arduino connected?")
            # We still show the UI, but maybe with a warning
            self.ui.show_error("Arduino Disconnected")
            self.root.mainloop()

if __name__ == "__main__":
    app = AutoPrintMain()
    app.run()
