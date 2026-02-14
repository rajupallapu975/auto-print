#!/usr/bin/env python3
"""
============================================================================
AUTO-PRINT SYSTEM - UNIFIED APPLICATION
============================================================================
Raspberry Pi auto-print kiosk system
All core functionality in one file for simplicity
============================================================================
"""

import tkinter as tk
import threading
import logging
import sys
import os
import requests
import time
import shutil
import io
from PIL import Image
import serial
import serial.tools.list_ports
import subprocess
import platform

# ============================================================================
# CONFIGURATION
# ============================================================================
CONFIG = {
    'BACKEND_URL': 'https://printer-backend-ch2e.onrender.com',
    'PRINTER_KEY': 'LOCAL_PRINTER',
    'ARDUINO_PORT': 'COM19' if sys.platform.startswith('win') else None,
    'TEMP_DIR': 'temp_jobs',
    'LOG_FILE': 'autoprint.log',
    'MAX_RETRIES': 2,
    'TIMEOUT': 15
}

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(
    filename=CONFIG['LOG_FILE'],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# BACKEND SERVICE
# ============================================================================
class BackendService:
    """Handles all backend API communication"""
    
    def __init__(self):
        self.base_url = CONFIG['BACKEND_URL']
        self.printer_key = CONFIG['PRINTER_KEY']
        self.temp_dir = CONFIG['TEMP_DIR']
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def verify_code(self, code):
        """Verify pickup code with backend"""
        url = f"{self.base_url}/verify-pickup-code"
        headers = {"x-printer-key": self.printer_key}
        code = str(code).strip()
        
        print(f"📡 Verifying: {code}")
        
        for attempt in range(CONFIG['MAX_RETRIES'] + 1):
            try:
                res = requests.post(
                    url,
                    json={"pickupCode": code},
                    headers=headers,
                    timeout=CONFIG['TIMEOUT']
                )
                
                if res.status_code == 404:
                    return {"success": False, "error": "INVALID_CODE"}
                if res.status_code == 403:
                    return {"success": False, "error": "AUTH_ERROR"}
                if res.status_code == 400:
                    data = res.json()
                    return {"success": False, "error": data.get("error", "Bad Request")}
                
                res.raise_for_status()
                data = res.json()
                
                if data.get("success"):
                    print(f"✅ Verified: {data.get('orderId')}")
                    return data
                return {"success": False, "error": data.get("error", "Unknown")}
                
            except requests.exceptions.Timeout:
                if attempt == CONFIG['MAX_RETRIES']:
                    return {"success": False, "error": "TIMEOUT"}
                time.sleep(1)
            except requests.exceptions.ConnectionError:
                if attempt == CONFIG['MAX_RETRIES']:
                    return {"success": False, "error": "CONNECTION_ERROR"}
                time.sleep(2)
            except Exception as e:
                logger.exception(f"Verify error: {e}")
                return {"success": False, "error": "SYSTEM_ERROR"}
        
        return {"success": False, "error": "CONNECTION_ERROR"}
    
    def download_files(self, verified_data):
        """Download files from Cloudinary"""
        order_id = verified_data.get("orderId")
        file_urls = verified_data.get("fileUrls", [])
        
        if not order_id or not file_urls:
            return {"success": False, "error": "MISSING_FILES"}
        
        job_dir = os.path.join(self.temp_dir, order_id)
        os.makedirs(job_dir, exist_ok=True)
        
        downloaded = []
        print(f"📥 Downloading {len(file_urls)} file(s)...")
        
        for idx, url in enumerate(file_urls):
            if not url:
                continue
            
            try:
                local_path = os.path.join(job_dir, f"file_{idx}.pdf")
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                
                content = r.content
                content_type = r.headers.get("Content-Type", "").lower()
                is_image = "image" in content_type or url.lower().endswith((".jpg", ".jpeg", ".png"))
                
                if is_image:
                    # Convert image to PDF
                    image = Image.open(io.BytesIO(content))
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(local_path, "PDF", resolution=100.0)
                else:
                    # Save PDF directly
                    with open(local_path, "wb") as f:
                        f.write(content)
                
                downloaded.append({"path": local_path})
                print(f"   ✅ [{idx+1}/{len(file_urls)}] Downloaded")
                
            except Exception as e:
                logger.error(f"Download failed: {e}")
        
        if not downloaded:
            return {"success": False, "error": "DOWNLOAD_ERROR"}
        
        print(f"✅ Downloaded {len(downloaded)} file(s)")
        return {"success": True, "files": downloaded}
    
    def mark_as_printed(self, order_id):
        """Mark order as printed and cleanup"""
        url = f"{self.base_url}/mark-printed"
        headers = {"x-printer-key": self.printer_key}
        
        try:
            res = requests.post(
                url,
                json={"orderId": order_id},
                headers=headers,
                timeout=10
            )
            
            if res.status_code == 200:
                print(f"✅ Marked as printed")
                # Cleanup
                job_dir = os.path.join(self.temp_dir, order_id)
                if os.path.exists(job_dir):
                    shutil.rmtree(job_dir)
        except Exception as e:
            logger.error(f"Mark printed failed: {e}")

# ============================================================================
# PRINTER SERVICE
# ============================================================================
class PrinterService:
    """Handles printer operations"""
    
    def __init__(self):
        self.printer_name = self._get_default_printer()
    
    def _get_default_printer(self):
        """Auto-detect default printer"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["powershell", "-Command", "(Get-WmiObject -Query 'SELECT * FROM Win32_Printer WHERE Default=$true').Name"],
                    capture_output=True,
                    text=True
                )
                return result.stdout.strip()
            else:
                # Linux/Raspberry Pi
                result = subprocess.run(["lpstat", "-d"], capture_output=True, text=True)
                if "system default destination:" in result.stdout:
                    return result.stdout.split(":")[-1].strip()
        except:
            pass
        return None
    
    def check_printer_available(self):
        """Check if printer is ready"""
        print("🔍 Checking printer status...")
        if not self.printer_name:
            print("❌ PRINTER NOT CONNECTED: No printer found")
            return False, "No printer found"
        print(f"✅ PRINTER CONNECTED: {self.printer_name}")
        return True, self.printer_name
    
    def print_job(self, files, settings):
        """Print files"""
        duplex = settings.get("duplex", False)
        
        for file_info in files:
            path = file_info.get("path")
            if not os.path.exists(path):
                continue
            
            try:
                if platform.system() == "Windows":
                    # Windows printing
                    subprocess.run(["start", "/min", path], shell=True)
                else:
                    # Linux/Raspberry Pi printing
                    cmd = ["lp"]
                    if self.printer_name:
                        cmd.extend(["-d", self.printer_name])
                    if duplex:
                        cmd.extend(["-o", "sides=two-sided-long-edge"])
                    cmd.append(path)
                    
                    subprocess.run(cmd, check=True)
                
                print(f"🖨️  Printed: {os.path.basename(path)}")
            except Exception as e:
                logger.error(f"Print failed: {e}")
                return False
        
        print(f"\n✅ ALL {len(files)} JOBS PRINTED SUCCESSFULLY")
        return True

# ============================================================================
# ARDUINO READER
# ============================================================================
class ArduinoReader:
    """Reads input from Arduino keypad"""
    
    def __init__(self, callback, port=None):
        self.callback = callback
        self.port = port
        self.serial = None
        self.running = False
    
    def _find_arduino(self):
        """Auto-detect Arduino port"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if 'Arduino' in port.description or 'CH340' in port.description:
                return port.device
        return None
    
    def start(self):
        """Start reading from Arduino"""
        if not self.port:
            self.port = self._find_arduino()
        
        if not self.port:
            return False
        
        try:
            self.serial = serial.Serial(self.port, 9600, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            self.running = True
            
            threading.Thread(target=self._read_loop, daemon=True).start()
            print(f"📡 Arduino connected: {self.port}")
            return True
        except Exception as e:
            logger.error(f"Arduino connection failed: {e}")
            return False
    
    def _read_loop(self):
        """Read loop"""
        while self.running:
            try:
                if self.serial and self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8').strip()
                    if line:
                        self.callback(line)
            except Exception as e:
                logger.error(f"Read error: {e}")
                time.sleep(0.1)

# ============================================================================
# GUI
# ============================================================================
class AutoPrintGUI:
    """Simple GUI for auto-print system"""
    
    def __init__(self, root, on_code_complete):
        self.root = root
        self.on_code_complete = on_code_complete
        self.current_code = ""
        
        # Setup UI
        self.root.geometry("800x480")
        self.root.configure(bg="#1a1a2e")
        
        # Title
        self.title = tk.Label(
            root,
            text="🖨️ AUTO-PRINT SYSTEM",
            font=("Arial", 32, "bold"),
            bg="#1a1a2e",
            fg="#00d4ff"
        )
        self.title.pack(pady=30)
        
        # Display
        self.display = tk.Label(
            root,
            text="Enter Pickup Code",
            font=("Courier", 28, "bold"),
            bg="#0f3460",
            fg="#ffffff",
            height=2
        )
        self.display.pack(pady=20, padx=40, fill=tk.X)
        
        # Status
        self.status = tk.Label(
            root,
            text="Ready",
            font=("Arial", 18),
            bg="#1a1a2e",
            fg="#95a5a6"
        )
        self.status.pack(pady=20)
    
    def handle_key_input(self, char):
        """Handle keypad input"""
        if char == "CLEAR":
            self.current_code = ""
        elif char == "BACKSPACE":
            self.current_code = self.current_code[:-1]
        elif char == "ENTER" or char == "#":
            if len(self.current_code) >= 4:
                self.on_code_complete(self.current_code)
                self.current_code = ""
        elif char.isdigit():
            self.current_code += char
        
        self.update_display()
    
    def update_display(self):
        """Update display"""
        if self.current_code:
            self.display.config(text=self.current_code)
        else:
            self.display.config(text="Enter Pickup Code")
    
    def show_error(self, msg):
        """Show error"""
        self.status.config(text=f"❌ {msg}", fg="#e74c3c")
        self.root.after(3000, lambda: self.status.config(text="Ready", fg="#95a5a6"))
    
    def show_success(self, msg):
        """Show success"""
        self.status.config(text=f"✅ {msg}", fg="#27ae60")
    
    def reset_ui(self, msg="Ready"):
        """Reset UI"""
        self.current_code = ""
        self.update_display()
        self.status.config(text=msg, fg="#95a5a6")

# ============================================================================
# MAIN APPLICATION
# ============================================================================
class AutoPrintApp:
    """Main application coordinator"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auto Print System")
        
        # Initialize services
        self.backend = BackendService()
        self.printer = PrinterService()
        
        # Initialize GUI
        self.gui = AutoPrintGUI(self.root, self.process_code)
        
        # Initialize Arduino
        self.arduino = ArduinoReader(
            callback=self.handle_keypad,
            port=CONFIG['ARDUINO_PORT']
        )
    
    def handle_keypad(self, char):
        """Handle keypad input"""
        mapping = {'B': '1', 'C': '2', 'D': '3', 'A': '0'}
        final_char = mapping.get(char, char)
        self.root.after(0, self.gui.handle_key_input, final_char)
    
    def process_code(self, code):
        """Process pickup code"""
        threading.Thread(
            target=self._workflow,
            args=(code,),
            daemon=True
        ).start()
    
    def _workflow(self, code):
        """Main workflow"""
        try:
            print(f"\n{'='*60}")
            print(f"🔎 Processing: {code}")
            print(f"{'='*60}\n")
            
            # Step 1: Verify
            verify_res = self.backend.verify_code(code)
            if not verify_res or not verify_res.get("success"):
                self.gui.show_error("Invalid Code")
                return
            
            order_id = verify_res.get("orderId")
            if not order_id:
                self.gui.show_error("Invalid Order")
                return
            
            self.gui.show_success("Code Verified!")
            
            # Step 2: Download
            download_res = self.backend.download_files(verify_res)
            if not download_res or not download_res.get("success"):
                self.gui.show_error("Download Failed")
                return
            
            files = download_res.get("files", [])
            if not files:
                self.gui.show_error("No Files")
                return
            
            # Step 3: Print (Directly after download)
            self.gui.show_success(f"Printing {len(files)} file(s)...")
            print_settings = verify_res.get("printSettings", {})
            
            success = self.printer.print_job(
                files,
                {"duplex": print_settings.get("doubleSide", False)}
            )
            
            if not success:
                self.gui.show_error("Printing Failed or Printer Unavailable")
                return
            
            # Step 4: Mark Complete
            self.backend.mark_as_printed(order_id)
            logger.info(f"Order {order_id} completed")
            
            self.gui.show_success("Complete!")
            self.root.after(5000, self.gui.reset_ui)
            
        except Exception as e:
            logger.exception(f"Workflow error: {e}")
            self.gui.show_error("System Error")
    
    def run(self):
        """Start application"""
        if self.arduino.start():
            print("\n" + "="*60)
            print("🚀 AUTO-PRINT SYSTEM ONLINE")
            print("="*60 + "\n")
            logger.info("System started")
        else:
            print("\n❌ Arduino not detected")
            self.gui.show_error("Arduino Disconnected")
        
        self.root.mainloop()

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    app = AutoPrintApp()
    app.run()
