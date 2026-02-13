import platform
import subprocess
import os
import time
import logging

logger = logging.getLogger(__name__)


class SmartPrinter:
    def __init__(self, printer_name=None):
        self.printer_name = printer_name
        self.os_type = platform.system()

    # ==========================================================
    # CHECK PRINTER
    # ==========================================================

    def check_printer_available(self):
        print("🔍 Checking printer status...")

        if self.os_type == "Windows":
            try:
                # Optimized PowerShell command to get printer status
                ps_cmd = "Get-Printer | Select-Object Name, PrinterStatus, JobCount, IsDefault"
                if self.printer_name:
                    ps_cmd = f"Get-Printer -Name '{self.printer_name}' | Select-Object Name, PrinterStatus, JobCount"

                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                if result.returncode == 0 and result.stdout.strip():
                    return True, f"Found: {result.stdout.strip().splitlines()[0]}"
                
                # Fallback: Just check if any printer exists
                fallback = subprocess.run(
                    ["powershell", "-Command", "Get-Printer | Select-Object -ExpandProperty Name"],
                    capture_output=True, text=True
                )
                if fallback.stdout.strip():
                    return True, "Printer(s) detected"

                return False, "No printer found"

            except Exception as e:
                logger.error(f"Windows printer check failed: {e}")
                return False, str(e)
        
        elif self.os_type == "Linux":
            try:
                result = subprocess.run(
                    ["lpstat", "-p"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and "printer" in result.stdout.lower():
                    # If specific printer requested, check it
                    if self.printer_name and self.printer_name not in result.stdout:
                        return False, f"Printer '{self.printer_name}' not in CuPS"
                    return True, "CUPS printer detected"

                return False, "No CUPS printer found"
            except Exception as e:
                return False, str(e)

        return False, "Unsupported OS"

    # ==========================================================
    # MAIN PRINT
    # ==========================================================

    def print_job(self, file_paths, settings):
        print("\n" + "=" * 50)
        print(f"🖨️  PRINTING ON {self.os_type.upper()}")
        print("=" * 50)

        available, message = self.check_printer_available()
        if not available:
            print(f"❌ Printer unavailable: {message}")
            return False

        success_count = 0
        total_to_print = len(file_paths)

        for idx, item in enumerate(file_paths):
            file_path = item if isinstance(item, str) else item.get("path")
            file_settings = {} if isinstance(item, str) else item.get("settings", {})
            
            # Merge settings
            job_settings = settings.copy() if settings else {}
            if file_settings:
                job_settings.update(file_settings)

            if not file_path or not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue

            print(f"📄 Processing [{idx+1}/{total_to_print}]: {os.path.basename(file_path)}")

            if self.os_type == "Windows":
                result = self._print_windows(file_path, job_settings)
            elif self.os_type == "Linux":
                result = self._print_linux(file_path, job_settings)
            else:
                print("⚠️ Unsupported OS")
                result = False

            if result:
                success_count += 1

        print(f"\n✨ {success_count}/{total_to_print} jobs submitted successfully\n")
        return success_count == total_to_print

    # ==========================================================
    # WINDOWS PRINT
    # ==========================================================

    def _print_windows(self, file_path, settings):
        try:
            abs_path = os.path.abspath(file_path)
            copies = settings.get("copies", 1)
            
            # For Windows, we use Start-Process with the Print verb
            # If a printer_name is specified, we try to use it
            if self.printer_name:
                print(f"   🎯 Target Printer: {self.printer_name}")
                # We can't directly specify printer name with 'Print' verb reliably across apps,
                # so we try the 'PrintTo' verb which is supported by many PDF viewers
                ps_command = f'Start-Process -FilePath "{abs_path}" -Verb PrintTo -ArgumentList "{self.printer_name}" -Wait'
            else:
                ps_command = f'Start-Process -FilePath "{abs_path}" -Verb Print -Wait'

            for c in range(int(copies)):
                print(f"   📤 Submitting copy {c+1}...")
                subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    timeout=45,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

            return True

        except Exception as e:
            print(f"❌ Windows print error: {e}")
            return False

    # ==========================================================
    # LINUX PRINT (RASPBERRY PI)
    # ==========================================================

    def _print_linux(self, file_path, settings):
        try:
            cmd = ["lp"]

            if self.printer_name:
                cmd.extend(["-d", self.printer_name])

            copies = settings.get("copies", 1)
            cmd.extend(["-n", str(copies)])

            color_mode = settings.get("color", "BW")
            if color_mode == "BW":
                cmd.extend(["-o", "ColorModel=Gray"])
            else:
                cmd.extend(["-o", "ColorModel=RGB"])

            if settings.get("duplex", False):
                cmd.extend(["-o", "sides=two-sided-long-edge"])

            if settings.get("orientation") == "LANDSCAPE":
                cmd.extend(["-o", "landscape"])

            cmd.append(file_path)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"CUPS error: {result.stderr}")
                print(f"❌ CUPS error: {result.stderr}")
                return False

            logger.info(f"Print job submitted: {result.stdout.strip()}")
            print(f"✅ CUPS Job: {result.stdout.strip()}")

            job_id = self._extract_job_id(result.stdout)
            if job_id:
                self.wait_for_job_completion(job_id, timeout=180)

            return True

        except subprocess.TimeoutExpired:
            print("❌ Print command timeout")
            return False
        except Exception as e:
            print(f"❌ Linux print error: {e}")
            return False

    # ==========================================================
    # EXTRACT JOB ID
    # ==========================================================

    def _extract_job_id(self, output):
        if "is" in output and "(" in output:
            return output.split("is ")[1].split(" (")[0]
        return None

    # ==========================================================
    # WAIT FOR COMPLETION (SAFE)
    # ==========================================================

    def wait_for_job_completion(self, job_id, timeout=180):
        print(f"⏳ Waiting for job {job_id}...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            res = subprocess.run(
                ["lpstat", "-W", "not-completed"],
                capture_output=True,
                text=True
            )

            if job_id not in res.stdout:
                print("✨ Job completed!")
                return True

            time.sleep(2)

        print("⚠️ Job timeout reached.")
        return False
