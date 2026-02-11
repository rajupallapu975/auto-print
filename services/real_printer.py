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

        for item in file_items:
            file_path = item if isinstance(item, str) else item.get("path")
            file_settings = {} if isinstance(item, str) else item.get("settings", {})

            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue

            success = False

            for attempt in range(self.max_retries + 1):
                try:
                    cmd = ["lp"]

                    # Printer selection
                    if self.printer_name:
                        cmd.extend(["-d", self.printer_name])

                    # Copies
                    copies = file_settings.get("copies", settings.get("copies", 1))
                    cmd.extend(["-n", str(copies)])

                    # Color mode
                    color_mode = file_settings.get("color", settings.get("color", "BW"))

                    if color_mode == "BW":
                        cmd.extend(["-o", "ColorModel=Gray"])
                    else:
                        cmd.extend(["-o", "ColorModel=RGB"])

                    # Duplex
                    duplex = settings.get("duplex", False)
                    if duplex:
                        cmd.extend(["-o", "sides=two-sided-long-edge"])

                    # Orientation
                    orientation = file_settings.get("orientation", "PORTRAIT")
                    if orientation == "LANDSCAPE":
                        cmd.extend(["-o", "landscape"])

                    cmd.append(file_path)

                    print(f"\n📄 Printing: {os.path.basename(file_path)}")
                    print(f"🔧 Command: {' '.join(cmd)}")

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        print(f"✅ Print submitted: {result.stdout.strip()}")
                        success = True
                        break
                    else:
                        print(f"⚠️ Print attempt failed: {result.stderr}")
                        time.sleep(2)

                except subprocess.TimeoutExpired:
                    print("❌ Print command timed out.")
                except Exception as e:
                    print(f"❌ Print error: {e}")

            if not success:
                print("❌ Failed to print after retries.")
                return False

        print("\n" + "=" * 50)
        print("✅ ALL PRINT JOBS COMPLETED")
        print("=" * 50 + "\n")

        return True
