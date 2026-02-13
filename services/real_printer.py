import subprocess
import os
import time


class RealPrinter:
    def __init__(self, printer_name=None, max_retries=1):
        self.printer_name = printer_name
        self.max_retries = max_retries

    # ==========================================================
    # CHECK PRINTER STATUS
    # ==========================================================

    def _is_printer_ready(self):
        try:
            result = subprocess.run(
                ["lpstat", "-p"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if self.printer_name:
                return self.printer_name in result.stdout
            return "printer" in result.stdout.lower()

        except Exception:
            return False

    # ==========================================================
    # PRINT JOB
    # ==========================================================

    def print_job(self, file_items, settings):
        print("\n" + "=" * 50)
        print("🖨️  REAL PRINT JOB STARTING")
        print("=" * 50)

        if not file_items:
            print("❌ No files provided.")
            return False

        if not self._is_printer_ready():
            print("❌ Printer not ready or not detected.")
            return False

        total_to_print = len(file_items)
        success_count = 0

        for idx, item in enumerate(file_items):
            file_path = item if isinstance(item, str) else item.get("path")
            file_settings = {} if isinstance(item, str) else item.get("settings", {})

            if not file_path or not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue

            success = False
            
            # Merge settings
            job_settings = settings.copy() if settings else {}
            if file_settings:
                job_settings.update(file_settings)

            for attempt in range(self.max_retries + 1):
                try:
                    cmd = ["lp"]

                    # Printer selection
                    if self.printer_name:
                        cmd.extend(["-d", self.printer_name])

                    # Copies (from merged settings)
                    copies = job_settings.get("copies", 1)
                    cmd.extend(["-n", str(copies)])

                    # Color mode
                    color_mode = job_settings.get("color", "BW")
                    if color_mode == "BW":
                        cmd.extend(["-o", "ColorModel=Gray"])
                    else:
                        cmd.extend(["-o", "ColorModel=RGB"])

                    # Duplex
                    if job_settings.get("duplex", False):
                        cmd.extend(["-o", "sides=two-sided-long-edge"])

                    # Orientation
                    if job_settings.get("orientation") == "LANDSCAPE":
                        cmd.extend(["-o", "landscape"])

                    cmd.append(file_path)

                    print(f"📄 Printing [{idx+1}/{total_to_print}]: {os.path.basename(file_path)}")
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        print(f"   ✅ Submitted: {result.stdout.strip()}")
                        success = True
                        break
                    else:
                        print(f"   ⚠️ Failed: {result.stderr}")
                        time.sleep(1)

                except Exception as e:
                    print(f"   ❌ Error: {e}")

            if success:
                success_count += 1

        print("\n" + "=" * 50)
        print(f"✨ {success_count}/{total_to_print} jobs submitted successfully")
        print("=" * 50 + "\n")

        return success_count == total_to_print
