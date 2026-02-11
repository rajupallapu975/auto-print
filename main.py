import tkinter as tk
import sys
import os
import time
import threading

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hardware.serial_reader import ArduinoSerialReader
from gui.app_interface import AutoPrintUI
from services.backend_service import BackendService
from services.smart_printer import SmartPrinter


class AutoPrintMain:
    def __init__(self):
        self.root = tk.Tk()

        # 🔗 Backend API URL (Render Production URL)
        self.backend = BackendService(
            base_url="https://printer-backend-ch2e.onrender.com"
        )

        self.printer = SmartPrinter(printer_name=None)

        # Initialize GUI
        self.ui = AutoPrintUI(
            self.root,
            on_code_complete=self.process_verification
        )

        # Hardware (Windows → COM19 | Raspberry Pi → auto-detect)
        arduino_port = "COM19" if sys.platform.startswith('win') else None
        self.reader = ArduinoSerialReader(
            port=arduino_port,
            callback=self.handle_keypad_input
        )

    # ============================================================
    # HANDLE KEYPAD INPUT
    # ============================================================

    def handle_keypad_input(self, char):
        print(f"⌨️ Keypad received: {char}")

        mapping = {
            'B': '1',
            'C': '2',
            'D': '3',
            'A': '0'
        }

        final_char = mapping.get(char, char)

        # Safe UI update from thread
        self.root.after(0, self.ui.handle_key_input, final_char)

    # ============================================================
    # PROCESS VERIFICATION (Threaded to prevent UI freeze)
    # ============================================================

    def process_verification(self, code):
        threading.Thread(
            target=self._process_verification_thread,
            args=(code,),
            daemon=True
        ).start()

    def _process_verification_thread(self, code):
        try:
            print(f"🔎 Verifying code: {code}")

            # 1️⃣ Verify with Backend
            verify_res = self.backend.verify_code(code)

            if not verify_res.get("success"):
                error_msg = verify_res.get("error", "Invalid code")

                if error_msg == "IP_ERROR":
                    self.root.after(
                        0,
                        self.ui.show_error,
                        "Backend Connection Error"
                    )
                else:
                    self.root.after(
                        0,
                        self.ui.show_error,
                        "Invalid or Expired Code"
                    )
                return

            order_id = verify_res.get("orderId")

            if not order_id:
                self.root.after(
                    0,
                    self.ui.show_error,
                    "Invalid Order ID"
                )
                return

            # 2️⃣ Download Files
            self.root.after(
                0,
                self.ui.show_success,
                "Code Verified! Preparing files..."
            )

            downloaded_items = self.backend.download_files(verify_res)

            if not downloaded_items:
                self.root.after(
                    0,
                    self.ui.show_error,
                    "File Download Failed"
                )
                return

            # 3️⃣ Print Files
            print_settings = verify_res.get("printSettings", {})
            global_duplex = print_settings.get("doubleSide", False)

            total_files = len(downloaded_items)

            for i, item in enumerate(downloaded_items):
                self.root.after(
                    0,
                    self.ui.update_printing_status,
                    i + 1,
                    total_files
                )

                final_settings = {
                    "copies": item.get("settings", {}).get("copies", 1),
                    "color": item.get("settings", {}).get("color", "BW"),
                    "duplex": global_duplex,
                    "orientation": item.get("settings", {}).get(
                        "orientation", "PORTRAIT"
                    ),
                }

                self.printer.print_job([item], final_settings)

            # 4️⃣ Mark Order as Printed
            self.backend.mark_as_printed(order_id)

            self.root.after(0, self.ui.show_success, "Printing Complete!")

            # Reset UI after 5 seconds
            self.root.after(
                5000,
                self.ui.reset_ui,
                "Ready for next customer"
            )

        except Exception as e:
            print(f"❌ System Error: {e}")
            self.root.after(
                0,
                self.ui.show_error,
                f"System Error: {str(e)}"
            )

    # ============================================================
    # RUN SYSTEM
    # ============================================================

    def run(self):
        if self.reader.start():
            print("🚀 System Online. Waiting for input...")
        else:
            print("❌ Arduino not detected.")
            self.ui.show_error("Arduino Disconnected")

        self.root.mainloop()


if __name__ == "__main__":
    app = AutoPrintMain()
    app.run()
