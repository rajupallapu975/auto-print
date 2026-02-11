import requests
import os
from PIL import Image
import io

class BackendError(Exception):
    """Custom exception for backend related errors."""
    pass

class DownloadError(Exception):
    """Custom exception for file download errors."""
    pass

class BackendService:
    def __init__(self, base_url="http://localhost:5000", base_dir="temp_jobs"):
        # Ensure base_url uses the port from your index.js (5000)
        self.base_url = base_url.rstrip("/")
        self.base_dir = base_dir
        try:
            os.makedirs(self.base_dir, exist_ok=True)
        except Exception as e:
            print(f"❌ Failed to create temp directory: {e}")

    def verify_code(self, pickup_code):
        """
        Asks the Backend to verify the code in Firebase.
        Returns the data which includes file URLs and print settings.
        """
        url = f"{self.base_url}/verify-pickup-code"
        print(f"📡 Verifying code at: {url}")
        try:
            headers = {"x-printer-key": "LOCAL_PRINTER"}
            res = requests.post(url, json={"pickupCode": pickup_code}, headers=headers, timeout=10)
            
            if res.status_code == 403:
                return {"success": False, "error": "AUTH_ERROR", "message": "Unauthorized Printer Key"}
            elif res.status_code == 404:
                return {"success": False, "error": "INVALID_CODE", "message": "Invalid or Expired Code"}
            
            res.raise_for_status()
            return res.json()
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Backend server is not reachable.")
            return {"success": False, "error": "IP_ERROR", "message": "Cannot reach backend server"}
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return {"success": False, "error": "SYSTEM_ERROR", "message": str(e)}

    def download_files(self, verified_data):
        """
        Takes the verified data from verify_code and downloads the files 
        using the direct URLs provided.
        """
        order_id = verified_data.get("orderId")
        # Backend now returns 'fileUrls' (Cloudinary links)
        file_urls = verified_data.get("fileUrls", []) 
        print_settings = verified_data.get("printSettings", {})
        
        if not order_id or not file_urls:
            print("❌ No files or Order ID found in verification data")
            return []

        job_dir = os.path.join(self.base_dir, order_id)
        try:
            os.makedirs(job_dir, exist_ok=True)
        except Exception as e:
            print(f"❌ Failed to create job directory {job_dir}: {e}")
            return []

        downloaded = []
        # Get individual file settings if they exist in metadata
        files_metadata = print_settings.get('files', [])

        for idx, url in enumerate(file_urls):
            # Extract filename from Cloudinary URL or index
            try:
                filename = url.split('/')[-1].split('?')[0]
                if not filename.endswith(('.pdf', '.jpg', '.png', '.jpeg')):
                    filename = f"file_{idx+1}.pdf"
                
                local_name = f"{idx}.pdf"
                local_path = os.path.join(job_dir, local_name)

                print(f"⬇️ Downloading: {filename}")
                r = requests.get(url, stream=True, timeout=15)
                r.raise_for_status()
                
                content = r.content
                
                # Image-to-PDF Conversion
                lower_name = filename.lower()
                if lower_name.endswith(('.jpg', '.jpeg', '.png')):
                    print(f"   🔄 Converting {filename} to PDF...")
                    try:
                        image = Image.open(io.BytesIO(content))
                        if image.mode in ("RGBA", "P"):
                            image = image.convert("RGB")
                        image.save(local_path, "PDF", resolution=100.0)
                    except Exception as img_err:
                        print(f"   ❌ Image conversion failed: {img_err}")
                        continue
                else:
                    # Save PDF directly
                    with open(local_path, "wb") as f:
                        f.write(content)
                
                # Link settings
                file_settings = files_metadata[idx] if idx < len(files_metadata) else {}
                downloaded.append({"path": local_path, "settings": file_settings})
                print(f"✅ Ready: {local_path}")

            except Exception as e:
                print(f"❌ Failed to process {url}: {e}")

        return downloaded

    def mark_as_printed(self, order_id):
        """
        Tells the backend to update Firebase and revoke the pickup code.
        """
        url = f"{self.base_url}/mark-printed"
        try:
            headers = {"x-printer-key": "LOCAL_PRINTER"}
            res = requests.post(url, json={"orderId": order_id}, headers=headers, timeout=5)
            if res.status_code == 200:
                print(f"✅ Order {order_id} marked as printed in Firebase")
            else:
                print(f"⚠️ Backend returned error marking as printed: {res.status_code}")
        except Exception as e:
            print(f"⚠️ Warning: Could not notify backend that order was printed: {e}")
