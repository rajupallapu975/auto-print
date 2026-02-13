import tkinter as tk
import sys
import os
import threading
import logging

# ============================================================
# LOGGING SETUP
# ============================================================

logging.basicConfig(
    filename='autoprint.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hardware.serial_reader import ArduinoSerialReader
from gui.app_interface import AutoPrintUI
from services.backend_service import BackendService
from services.smart_printer import SmartPrinter


class AutoPrintMain:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auto Print System")

        # Backend API
        self.backend = BackendService(
            base_url="https://printer-backend-ch2e.onrender.com"
        )

        # Printer
        self.printer = SmartPrinter(printer_name=None)

        # GUI
        self.ui = AutoPrintUI(
            self.root,
            on_code_complete=self.process_verification
        )

        # Arduino Port
        arduino_port = "COM19" if sys.platform.startswith('win') else None
        self.reader = ArduinoSerialReader(
            port=arduino_port,
            callback=self.handle_keypad_input
        )

    # ============================================================
    # HANDLE KEYPAD INPUT
    # ============================================================

    def handle_keypad_input(self, char):
        mapping = {
            'B': '1',
            'C': '2',
            'D': '3',
            'A': '0'
        }

        final_char = mapping.get(char, char)
        self.root.after(0, self.ui.handle_key_input, final_char)

    # ============================================================
    # PROCESS VERIFICATION (THREAD SAFE)
    # ============================================================

    def process_verification(self, code):
        threading.Thread(
            target=self._process_verification_thread,
            args=(code,),
            daemon=True
        ).start()

    def _process_verification_thread(self, code):
        try:
            logger.info(f"Verifying code: {code}")
            print(f"🔎 Verifying code: {code}")

            # 1️⃣ VERIFY CODE
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

            # 2️⃣ DOWNLOAD FILES
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

            # 3️⃣ CHECK PRINTER
            printer_status, printer_msg = self.printer.check_printer_available()

            if not printer_status:
                logger.error(f"Printer error: {printer_msg}")
                self.root.after(0, self.ui.show_error, "Printer Not Found")
                return

            logger.info(f"Printer ready: {printer_msg}")

            # 4️⃣ PRINT FILES
            self.root.after(
                0,
                self.ui.show_status,
                f"Printing {len(files)} files..."
            )

            print_settings = verify_res.get("printSettings", {})
            duplex = print_settings.get("doubleSide", False)

            print_success = self.printer.print_job(
                files,
                {"duplex": duplex}
            )

            if not print_success:
                logger.error("Printing failed")
                self.root.after(0, self.ui.show_error, "Printing Failed")
                return

            logger.info("Printing successful")

            # 5️⃣ MARK ORDER AS PRINTED
            self.backend.mark_as_printed(order_id)
            logger.info(f"Order {order_id} marked as printed")

            self.root.after(0, self.ui.show_success, "Printing Complete!")

            # Reset UI after 5 seconds
            self.root.after(
                5000,
                self.ui.reset_ui,
                "Ready for next customer"
            )

        except Exception as e:
            logger.exception(f"Critical system error: {e}")
            self.root.after(0, self.ui.show_error, "System Error")

    # ============================================================
    # RUN SYSTEM
    # ============================================================

    def run(self):
        if self.reader.start():
            print("🚀 System Online. Waiting for input...")
            logger.info("System started successfully")
        else:
            print("❌ Arduino not detected.")
            logger.error("Arduino not detected")
            self.ui.show_error("Arduino Disconnected")

        self.root.mainloop()


if __name__ == "__main__":
    app = AutoPrintMain()
    app.run()
