from firebase_service import FirebaseService
from backend_service import BackendService
# from fake_printer import FakePrinter  # For testing only
# from real_printer import RealPrinter  # For Linux only
from smart_printer import SmartPrinter  # Works on Windows & Linux

def main():
    print("\n--- RASPBERRY PI AUTO-PRINT MODULE ---")

    # 🔗 Backend base URL (index.js)
    BACKEND_BASE_URL = "http://localhost:5000"
    
    # 🖨️ Printer Configuration
    # Find your printer name with: lpstat -p -d
    # Leave as None to use default printer
    PRINTER_NAME = None  # Example: "HP_LaserJet_Pro"

    # Initialize services
    fb_service = FirebaseService()
    backend = BackendService(base_url=BACKEND_BASE_URL)
    printer = SmartPrinter(printer_name=PRINTER_NAME)
    
    # Check printer before starting
    is_available, message = printer.check_printer_available()
    if not is_available:
        print(f"\n⚠️ WARNING: {message}")
        response = input("Continue anyway? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("👋 Exiting. Please connect a printer and try again.")
            return
        print("⚠️ Proceeding without printer verification...\n")

    while True:
        print("\n" + "-" * 40)
        pickup_code = input("⌨️  Enter Pickup Code (or 'exit' to quit): ").strip()

        if pickup_code.lower() == "exit":
            print("👋 Exiting auto-print module")
            break

        # 1️⃣ Get order using pickup code (Firestore)
        order_data = fb_service.get_order_by_pickup_code(pickup_code)
        if not order_data:
            continue

        # 2️⃣ Download files using Order ID (Node backend)
        downloaded_items = backend.download_files(order_data)
        if not downloaded_items:
            print("❌ No files downloaded. Aborting print.")
            continue

        # 3️⃣ Print files with actual settings
        print(f"\n📑 Preparing {len(downloaded_items)} files for printing...\n")
        
        # Get global settings from order
        print_settings = order_data.get('printSettings', {})
        global_duplex = print_settings.get('doubleSide', False)

        for item in downloaded_items:
            file_path = item["path"]
            file_settings = item.get("settings", {})
            
            # Combine global and per-file settings
            final_settings = {
                "copies": file_settings.get('copies', 1),
                "color": file_settings.get('color', 'BW'),
                "duplex": global_duplex,
                "orientation": file_settings.get('orientation', 'PORTRAIT'),
            }

            printer.print_job([item], final_settings)

        print("✅ PRINT JOBS COMPLETED")

if __name__ == "__main__":
    main()
