import requests
import os
from PIL import Image
import io

class BackendService:
    def __init__(self, base_url="http://localhost:5000", base_dir="temp_jobs"):
        # Ensure base_url uses the port from your index.js (5000)
        self.base_url = base_url.rstrip("/")
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def verify_code(self, pickup_code):
        """
        New method: Asks the Backend to verify the code in Supabase.
        Returns the data which includes file URLs and print settings.
        """
        url = f"{self.base_url}/verify-pickup-code"
        print(f"📡 Verifying code at: {url}")
        try:
            res = requests.post(url, json={"pickupCode": pickup_code}, timeout=10)
            res.raise_for_status()
            return res.json() # Returns {'success': True, 'orderId': '...', 'files': [...]}
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Backend server is not reachable.")
            return {"success": False, "error": "IP_ERROR"}
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return {"success": False, "error": str(e)}

    def download_files(self, verified_data):
        """
        Takes the verified data from verify_code and downloads the files 
        using the direct Supabase URLs provided.
        """
        order_id = verified_data.get("orderId")
        files_list = verified_data.get("files", []) # list of {'name': '...', 'url': '...'}
        print_settings = verified_data.get("printSettings", {})
        
        if not order_id or not files_list:
            print("❌ No files or Order ID found in verification data")
            return []

        job_dir = os.path.join(self.base_dir, order_id)
        os.makedirs(job_dir, exist_ok=True)

        downloaded = []
        # Get individual file settings if they exist in metadata
        files_metadata = print_settings.get('files', [])

        for idx, file_info in enumerate(files_list):
            filename = file_info.get("name")
            download_url = file_info.get("url")
            
            # Save locally as PDF
            local_name = f"{idx}.pdf"
            local_path = os.path.join(job_dir, local_name)

            try:
                print(f"⬇️ Downloading: {filename}")
                r = requests.get(download_url, stream=True, timeout=15)
                r.raise_for_status()
                
                content = r.content
                
                # Image-to-PDF Conversion
                lower_name = filename.lower()
                if lower_name.endswith(('.jpg', '.jpeg', '.png')):
                    print(f"   🔄 Converting {filename} to PDF...")
                    image = Image.open(io.BytesIO(content))
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(local_path, "PDF", resolution=100.0)
                else:
                    # Save PDF directly
                    with open(local_path, "wb") as f:
                        f.write(content)
                
                # Link settings
                file_settings = files_metadata[idx] if idx < len(files_metadata) else {}
                downloaded.append({"path": local_path, "settings": file_settings})
                print(f"✅ Ready: {local_path}")

            except Exception as e:
                print(f"❌ Failed to process {filename}: {e}")

        return downloaded

    def mark_as_printed(self, order_id):
        """
        Tells the backend to update Supabase and revoke the pickup code.
        """
        url = f"{self.base_url}/mark-printed"
        try:
            requests.post(url, json={"orderId": order_id}, timeout=5)
            print(f"✅ Order {order_id} marked as printed in Supabase")
        except:
            print(f"⚠️ Warning: Could not notify backend that order was printed")
