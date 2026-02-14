# ============================================================================
# AUTO-PRINT MAIN APPLICATION
# ============================================================================
# Raspberry Pi auto-print kiosk system
# Integrates: Arduino keypad, GUI, Backend API, and Printer
# ============================================================================

import tkinter as tk
import sys
import os
import threading
import logging

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
logging.basicConfig(
    filename='autoprint.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# IMPORT MODULES
# ============================================================================
from hardware.serial_reader import ArduinoSerialReader
from gui.app_interface import AutoPrintUI
from services.backend_service import BackendService
from services.smart_printer import SmartPrinter

# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================
class AutoPrintMain:
    """
    Main application class that coordinates all components:
    - Arduino keypad input
    - GUI display
    - Backend communication
    - Printer control
    """
    
    def __init__(self):
        # Initialize Tkinter root window
        self.root = tk.Tk()
        self.root.title("Auto Print System")
        
        # ====================================================================
        # INITIALIZE BACKEND SERVICE
        # ====================================================================
        self.backend = BackendService(
            base_url="https://printer-backend-ch2e.onrender.com"
        )
        
        # ====================================================================
        # INITIALIZE PRINTER
        # ====================================================================
        self.printer = SmartPrinter(printer_name=None)  # Auto-detect printer
        
        # ====================================================================
        # INITIALIZE GUI
        # ====================================================================
        self.ui = AutoPrintUI(
            self.root,
            on_code_complete=self.process_verification
        )
        
        # ====================================================================
        # INITIALIZE ARDUINO SERIAL READER
        # ====================================================================
        # Use COM19 on Windows, auto-detect on Linux/Raspberry Pi
        arduino_port = "COM19" if sys.platform.startswith('win') else None
        self.reader = ArduinoSerialReader(
            port=arduino_port,
            callback=self.handle_keypad_input
        )
    
    # ========================================================================
    # KEYPAD INPUT HANDLER
    # ========================================================================
    def handle_keypad_input(self, char):
        """
        Handle input from Arduino keypad.
        Maps special keys (A, B, C, D) to numbers.
        
        Args:
            char (str): Character received from Arduino
        """
        # Key mapping for 4x4 keypad
        mapping = {
            'B': '1',
            'C': '2',
            'D': '3',
            'A': '0'
        }
        
        final_char = mapping.get(char, char)
        
        # Update GUI (must be done in main thread)
        self.root.after(0, self.ui.handle_key_input, final_char)
    
    # ========================================================================
    # VERIFICATION PROCESS (MAIN WORKFLOW)
    # ========================================================================
    def process_verification(self, code):
        """
        Process pickup code verification in a separate thread.
        This is the main workflow that handles the entire print job.
        
        Args:
            code (str): 6-digit pickup code
        """
        threading.Thread(
            target=self._process_verification_thread,
            args=(code,),
            daemon=True
        ).start()
    
    def _process_verification_thread(self, code):
        """
        Main verification and printing workflow.
        Runs in a separate thread to avoid blocking the GUI.
        
        Steps:
        1. Verify code with backend
        2. Download files from Cloudinary
        3. Check printer status
        4. Print files
        5. Mark order as completed
        """
        try:
            logger.info(f"Verifying code: {code}")
            print(f"\n{'='*60}")
            print(f"🔎 VERIFYING CODE: {code}")
            print(f"{'='*60}\n")
            
            # ================================================================
            # STEP 1: VERIFY CODE WITH BACKEND
            # ================================================================
            verify_res = self.backend.verify_code(code)
            
            if not verify_res or not verify_res.get("success"):
                error_msg = verify_res.get("error", "Invalid Code") if verify_res else "Backend Error"
                logger.warning(f"Verification failed: {error_msg}")
                self.root.after(0, self.ui.show_error, "Invalid or Expired Code")
                return
            
            order_id = verify_res.get("orderId")
            if not order_id:
                logger.error("Order ID missing in verification response")
                self.root.after(0, self.ui.show_error, "Invalid Order ID")
                return
            
            self.root.after(
                0,
                self.ui.show_success,
                "Code Verified! Preparing files..."
            )
            
            # ================================================================
            # STEP 2: DOWNLOAD FILES FROM CLOUDINARY
            # ================================================================
            logger.info("Downloading files...")
            download_res = self.backend.download_files(verify_res)
            
            if not download_res or not download_res.get("success"):
                logger.error("Download failed")
                self.root.after(0, self.ui.show_error, "Download Failed")
                return
            
            files = download_res.get("files", [])
            if not files:
                logger.error("No files returned from backend")
                self.root.after(0, self.ui.show_error, "No Files Found")
                return
            
            logger.info(f"{len(files)} files downloaded")
            
            # ================================================================
            # STEP 3: PRINT FILES (Directly after download)
            # ================================================================
            self.root.after(
                0,
                self.ui.show_success,
                "Printing in progress..."
            )
            
            print_settings = verify_res.get("printSettings", {})
            duplex = print_settings.get("doubleSide", False)
            
            print_success = self.printer.print_job(
                files,
                {"duplex": duplex}
            )
            
            if not print_success:
                logger.error("Printing failed or printer unavailable")
                self.root.after(0, self.ui.show_error, "Printing Failed")
                return
            
            logger.info("Printing successful")
            
            # ================================================================
            # STEP 5: MARK ORDER AS PRINTED
            # ================================================================
            self.backend.mark_as_printed(order_id)
            logger.info(f"Order {order_id} marked as printed")
            
            self.root.after(0, self.ui.show_success, "Printed Successfully!")
            
            # Reset UI after 5 seconds
            self.root.after(
                5000,
                self.ui.reset_ui,
                "Ready for next customer"
            )
        
        except Exception as e:
            logger.exception(f"Critical system error: {e}")
            self.root.after(0, self.ui.show_error, "System Error")
    
    # ========================================================================
    # RUN APPLICATION
    # ========================================================================
    def run(self):
        """
        Start the application.
        Initializes Arduino reader and starts the Tkinter main loop.
        """
        if self.reader.start():
            print("\n" + "="*60)
            print("🚀 AUTO-PRINT SYSTEM ONLINE")
            print("="*60)
            print("Waiting for pickup codes...")
            print("="*60 + "\n")
            logger.info("System started successfully")
        else:
            print("\n❌ Arduino not detected.")
            logger.error("Arduino not detected")
            self.ui.show_error("Arduino Disconnected")
        
        # Start Tkinter main loop
        self.root.mainloop()

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    app = AutoPrintMain()
    app.run()
