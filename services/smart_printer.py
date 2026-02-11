import platform
import subprocess
import os
import time


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
                ps_cmd = (
                    "Get-WmiObject -Class Win32_Printer | "
                    "Where-Object {$_.Default -eq $true} | "
                    "Select-Object -ExpandProperty Name"
                )

                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.stdout.strip():
                    return True, result.stdout.strip()

                return False, "No default printer"

            except Exception as e:
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
        print(f"🖨️ PRINTING ON {self.os_type.upper()}")
        print("=" * 50)

        available, message = self.check_printer_available()
        if not available:
            print(f"❌ Printer unavailable: {message}")
            return False

        success_count = 0

        for item in file_paths:
            file_path = item if isinstance(item, str) else item.get("path")
            file_settings = {} if isinstance(item, str) else item.get("settings", {})

            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue

            if self.os_type == "Windows":
                result = self._print_windows(file_path, file_settings, settings)
            elif self.os_type == "Linux":
                result = self._print_linux(file_path, file_settings, settings)
            else:
                print("⚠️ Unsupported OS")
                result = False

            if result:
                success_count += 1

        print(f"\n✅ {success_count}/{len(file_paths)} printed\n")
        return success_count > 0

    # ==========================================================
    # WINDOWS PRINT
    # ==========================================================

    def _print_windows(self, file_path, file_settings, settings):
        try:
            abs_path = os.path.abspath(file_path)
            copies = file_settings.get("copies", settings.get("copies", 1))

            ps_command = f'Start-Process -FilePath "{abs_path}" -Verb Print -Wait'

            for _ in range(copies):
                subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    timeout=30
                )

            print("✅ Windows print submitted")
            return True

        except Exception as e:
            print(f"❌ Windows print error: {e}")
            return False

    # ==========================================================
    # LINUX PRINT (RASPBERRY PI)
    # ==========================================================

    def _print_linux(self, file_path, file_settings, settings):
        try:
            cmd = ["lp"]

            if self.printer_name:
                cmd.extend(["-d", self.printer_name])

            copies = file_settings.get("copies", settings.get("copies", 1))
            cmd.extend(["-n", str(copies)])

            color_mode = file_settings.get("color", settings.get("color", "BW"))
            if color_mode == "BW":
                cmd.extend(["-o", "ColorModel=Gray"])
            else:
                cmd.extend(["-o", "ColorModel=RGB"])

            if settings.get("duplex", False):
                cmd.extend(["-o", "sides=two-sided-long-edge"])

            if file_settings.get("orientation") == "LANDSCAPE":
                cmd.extend(["-o", "landscape"])

            cmd.append(file_path)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"❌ CUPS error: {result.stderr}")
                return False

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
