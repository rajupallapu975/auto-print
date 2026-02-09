import requests
import os

class BackendService:
    def __init__(self, base_url="http://localhost:3000", base_dir="temp_jobs"):
        self.base_url = base_url.rstrip("/")
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def download_files(self, order_data):
        order_id = order_data.get("id")
        if not order_id:
            print("❌ Order ID missing")
            return []

        job_dir = os.path.join(self.base_dir, order_id)
        os.makedirs(job_dir, exist_ok=True)

        # 1️⃣ Get file list
        list_url = f"{self.base_url}/api/get-files/{order_id}"
        print(f"🔎 Querying files: {list_url}")

        try:
            res = requests.get(list_url, timeout=5)
            res.raise_for_status()
            files = res.json().get("files", [])
            print(f"📄 Backend reported files: {files}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Backend IP Error: Could not connect to {self.base_url}. Check if LAPTOP_IP is correct.")
            return "IP_ERROR"
        except Exception as e:
            print(f"❌ Backend error: {e}")
            return []

        downloaded = []
        print_settings = order_data.get('printSettings', {})
        files_metadata = print_settings.get('files', [])

        # 2️⃣ Download each file and convert to PDF if needed
        for idx, name in enumerate(files):
            url = f"{self.base_url}/api/download/{order_id}/{name}"
            
            # Always save as PDF (convert if needed)
            pdf_name = f"{idx}.pdf"
            local_path = os.path.join(job_dir, pdf_name)

            try:
                print(f"⬇️ Downloading: {url}")
                r = requests.get(url, stream=True, timeout=10)
                r.raise_for_status()
                
                content = r.content
                
                # Check if it's an image that needs conversion
                lower_name = name.lower()
                if lower_name.endswith(('.jpg', '.jpeg', '.png')):
                    print(f"   🔄 Converting {name} to PDF...")
                    from PIL import Image
                    import io
                    
                    image = Image.open(io.BytesIO(content))
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(local_path, "PDF", resolution=100.0)
                else:
                    # Already PDF, save directly
                    with open(local_path, "wb") as f:
                        f.write(content)
                
                # Get settings for this file from metadata
                file_settings = {}
                if idx < len(files_metadata):
                    file_settings = files_metadata[idx]

                downloaded.append({"path": local_path, "settings": file_settings})
                print(f"✅ Saved: {local_path}")

            except Exception as e:
                print(f"❌ Failed to download {name}: {e}")

        return downloaded
