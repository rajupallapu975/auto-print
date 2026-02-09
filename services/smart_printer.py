import platform
import subprocess
import os

class SmartPrinter:
    """
    Cross-platform printer that works on both Windows and Linux.
    - Windows: Uses default printer via PowerShell
    - Linux/Raspberry Pi: Uses CUPS (lp command)
    """
    
    def __init__(self, printer_name=None):
        self.printer_name = printer_name
        self.os_type = platform.system()
        
    def check_printer_available(self):
        """
        Checks if a printer is available and ready.
        Returns (bool, str) - (is_available, message)
        """
        print("\n🔍 Checking printer status...")
        
        if self.os_type == "Windows":
            try:
                # Get default printer
                ps_cmd = "Get-WmiObject -Class Win32_Printer | Where-Object {$_.Default -eq $true} | Select-Object -ExpandProperty Name"
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    printer_name = result.stdout.strip()
                    print(f"✅ Default printer found: {printer_name}")
                    return True, printer_name
                else:
                    print("❌ No default printer configured")
                    return False, "No default printer found"
                    
            except Exception as e:
                print(f"⚠️ Could not check printer: {e}")
                return False, str(e)
                
        elif self.os_type == "Linux":
            try:
                # Check CUPS printers
                result = subprocess.run(
                    ["lpstat", "-p", "-d"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    print(f"✅ Printer(s) available:\n{result.stdout}")
                    return True, "CUPS printers found"
                else:
                    print("❌ No printers found in CUPS")
                    return False, "No CUPS printers"
                    
            except FileNotFoundError:
                print("❌ CUPS not installed (run: sudo apt-get install cups)")
                return False, "CUPS not installed"
            except Exception as e:
                print(f"⚠️ Could not check printer: {e}")
                return False, str(e)
        else:
            print(f"⚠️ Unsupported OS: {self.os_type}")
            return False, f"Unsupported OS: {self.os_type}"
        
    def print_job(self, file_paths, settings):
        """
        Sends files to printer based on OS.
        """
        print("\n" + "="*40)
        print(f"🖨️  PRINTING ON {self.os_type.upper()}")
        print("="*40)
        
        if not file_paths:
            print("❌ No files provided for printing.")
            return False

        success_count = 0
        
        for item in file_paths:
            file_path = item if isinstance(item, str) else item.get('path')
            file_settings = {} if isinstance(item, str) else item.get('settings', {})
            
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue
                
            print(f"\n📄 Printing: {os.path.basename(file_path)}")
            
            if self.os_type == "Windows":
                result = self._print_windows(file_path, file_settings, settings)
            elif self.os_type == "Linux":
                result = self._print_linux(file_path, file_settings, settings)
            else:
                print(f"⚠️ Unsupported OS: {self.os_type}")
                result = False
                
            if result:
                success_count += 1
        
        print("\n" + "="*40)
        print(f"✅ {success_count}/{len(file_paths)} FILES PRINTED")
        print("="*40 + "\n")
        return success_count > 0
    
    def _print_windows(self, file_path, file_settings, settings):
        """Print using Windows default printer."""
        try:
            # Convert to absolute path (Windows requires it)
            abs_path = os.path.abspath(file_path)
            
            copies = file_settings.get('copies', settings.get('copies', 1))
            
            print(f"   Copies: {copies}")
            print(f"   Color: {file_settings.get('color', 'BW')}")
            print(f"   Path: {abs_path}")
            
            # Windows PowerShell print command with absolute path
            ps_command = f'Start-Process -FilePath "{abs_path}" -Verb Print -Wait'
            
            # Print multiple times for copies (simple approach)
            for i in range(copies):
                if copies > 1:
                    print(f"   Printing copy {i+1}/{copies}...")
                    
                result = subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"❌ Print failed: {result.stderr}")
                    return False
            
            print(f"✅ Sent to Windows printer")
            return True
            
        except Exception as e:
            print(f"❌ Windows print error: {e}")
            return False
    
    def _print_linux(self, file_path, file_settings, settings):
        """Print using CUPS (Linux/Raspberry Pi)."""
        try:
            cmd = ['lp']
            
            if self.printer_name:
                cmd.extend(['-d', self.printer_name])
            
            # Copies
            copies = file_settings.get('copies', settings.get('copies', 1))
            cmd.extend(['-n', str(copies)])
            
            # Color
            color_mode = file_settings.get('color', settings.get('color', 'BW'))
            if color_mode == 'BW':
                cmd.extend(['-o', 'ColorModel=Gray'])
            else:
                cmd.extend(['-o', 'ColorModel=RGB'])
            
            # Duplex
            duplex = settings.get('duplex', False)
            if duplex:
                cmd.extend(['-o', 'sides=two-sided-long-edge'])
            
            # Orientation
            orientation = file_settings.get('orientation', 'PORTRAIT')
            if orientation == 'LANDSCAPE':
                cmd.extend(['-o', 'landscape'])
            
            cmd.append(file_path)
            
            print(f"🔧 Command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract Job ID (e.g., "request id is HL-L2350DW-123 (1 file(s))")
                output = result.stdout.strip()
                print(f"✅ Job Sent: {output}")
                
                # Extract job id if possible
                job_id = None
                if "is" in output and "(" in output:
                    job_id = output.split("is ")[1].split(" (")[0]
                
                # WAIT UNTIL PRINTED (Optional but requested)
                if job_id:
                    self.wait_for_job_completion(job_id)
                
                return True
            else:
                print(f"❌ CUPS error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Linux print error: {e}")
            return False

    def wait_for_job_completion(self, job_id):
        """Polls CUPS until the job is no longer in the active queue."""
        import time
        print(f"⏳ Waiting for printer to finish job: {job_id}...")
        
        while True:
            # lpstat -W not-completed shows current jobs
            res = subprocess.run(["lpstat", "-W", "not-completed"], capture_output=True, text=True)
            if job_id not in res.stdout:
                # Job is no longer in 'not-completed' list
                print(f"✨ Job {job_id} finished printing!")
                break
            time.sleep(2) # Poll every 2 seconds
