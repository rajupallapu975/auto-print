import os

class FakePrinter:
    def print_job(self, file_paths, settings):
        print("\n" + "="*40)
        print("🖨️  SIMULATED PRINT JOB")
        print("="*40)

        for f in file_paths:
            print(f"📄 {os.path.basename(f)}")

        print("⚙️ Settings:", settings)
        print("✅ TEST MODE – NO REAL PRINT")
        print("="*40)
