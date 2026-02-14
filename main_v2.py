"""
Auto-Print System - Main Entry Point
Streamlined, efficient architecture with clear sections
"""
import tkinter as tk
import threading
import logging
from config import *

# ============================================================
# LOGGING SETUP
# ============================================================
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# IMPORTS
# ============================================================
from hardware.serial_reader import ArduinoSerialReader
from gui.app_interface import AutoPrintUI
from services.backend_service import BackendService
from services.smart_printer import SmartPrinter


# ============================================================
# MAIN APPLICATION CLASS
# ============================================================
class AutoPrintSystem:
    def __init__(self):
        """Initialize all system components"""
        self.root = tk.Tk()
        self.root.title("Auto Print System")
        
        # Initialize services
        self.backend = BackendService(base_url=BACKEND_URL)
        self.printer = SmartPrinter(printer_name=PRINTER_NAME)
        
        # Initialize UI
        self.ui = AutoPrintUI(self.root, on_code_complete=self.verify_and_print)
        
        # Initialize hardware
        self.reader = ArduinoSerialReader(
            port=ARDUINO_PORT,
            callback=self._handle_keypad
        )
    
    # ============================================================
    # HARDWARE INPUT HANDLER
    # ============================================================
    def _handle_keypad(self, char):
        """Process keypad input with character mapping"""
        mapping = {'B': '1', 'C': '2', 'D': '3', 'A': '0'}
        final_char = mapping.get(char, char)
        self.root.after(0, self.ui.handle_key_input, final_char)
    
    # ============================================================
    # CORE PRINTING WORKFLOW
    # ============================================================
    def verify_and_print(self, code):
        """Main workflow: Verify -> Download -> Print"""
        threading.Thread(
            target=self._print_workflow,
            args=(code,),
            daemon=True
        ).start()
    
    def _print_workflow(self, code):
        """Execute complete print workflow in background thread"""
        try:
            logger.info(f"Processing code: {code}")
            
            # Step 1: Verify
            verify_res = self.backend.verify_code(code)
            if not verify_res or not verify_res.get("success"):
                self._show_error("Invalid or Expired Code")
                return
            
            order_id = verify_res.get("orderId")
            if not order_id:
                self._show_error("Invalid Order ID")
                return
            
            self._show_status("Code Verified! Preparing files...")
            
            # Step 2: Download
            download_res = self.backend.download_files(verify_res)
            if not download_res or not download_res.get("success"):
                self._show_error("Download Failed")
                return
            
            files = download_res.get("files", [])
            if not files:
                self._show_error("No Files Found")
                return
            
            # Step 3: Print (Directly after download)
            self._show_status("Printing in progress...")
            print_settings = verify_res.get("printSettings", {})
            
            success = self.printer.print_job(
                files,
                {"duplex": print_settings.get("doubleSide", False)}
            )
            
            if not success:
                self._show_error("Printing Failed or Printer Unavailable")
                return
            
            logger.info("Printing successful")
            # Step 4: Mark Complete
            self.backend.mark_as_printed(order_id)
            logger.info(f"Order {order_id} completed")
            
            self._show_success("Printed Successfully!")
            self.root.after(5000, self.ui.reset_ui, "Ready")
            
        except Exception as e:
            logger.exception(f"System error: {e}")
            self._show_error("System Error")
    
    # ============================================================
    # UI HELPERS
    # ============================================================
    def _show_error(self, msg):
        self.root.after(0, self.ui.show_error, msg)
    
    def _show_status(self, msg):
        self.root.after(0, self.ui.show_success, msg)
    
    def _show_success(self, msg):
        self.root.after(0, self.ui.show_success, msg)
    
    # ============================================================
    # RUN SYSTEM
    # ============================================================
    def run(self):
        """Start the system"""
        if self.reader.start():
            print("🚀 System Online")
            logger.info("System started")
        else:
            print("❌ Arduino not detected")
            logger.error("Arduino not detected")
            self.ui.show_error("Arduino Disconnected")
        
        self.root.mainloop()


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    app = AutoPrintSystem()
    app.run()
