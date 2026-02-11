import requests
import os
from PIL import Image
import io
import shutil
import time


class BackendService:
    def __init__(
        self,
        base_url="http://localhost:5000",
        base_dir="temp_jobs",
        printer_key="LOCAL_PRINTER",
        max_retries=2
    ):
        self.base_url = base_url.rstrip("/")
        self.base_dir = base_dir
        self.printer_key = printer_key
        self.max_retries = max_retries

        os.makedirs(self.base_dir, exist_ok=True)

    # ==========================================================
    # VERIFY CODE
    # ==========================================================

    def verify_code(self, pickup_code):
        url = f"{self.base_url}/verify-pickup-code"
        headers = {"x-printer-key": self.printer_key}

        print(f"📡 Verifying code: {pickup_code}")

        for attempt in range(self.max_retries + 1):
            try:
                res = requests.post(
                    url,
                    json={"pickupCode": pickup_code},
                    headers=headers,
                    timeout=10
                )

                if res.status_code == 403:
                    return {"success": False, "error": "AUTH_ERROR"}

                if res.status_code == 404:
                    return {"success": False, "error": "INVALID_CODE"}

                res.raise_for_status()

                data = res.json()

                if not data.get("success", False):
                    return {"success": False, "error": "INVALID_RESPONSE"}

                return data

            except requests.exceptions.ConnectionError:
                print("⚠️ Backend unreachable. Retrying...")
                time.sleep(2)

            except Exception as e:
                print(f"❌ Verification error: {e}")
                return {"success": False, "error": "SYSTEM_ERROR"}

        return {"success": False, "error": "IP_ERROR"}

    # ==========================================================
    # DOWNLOAD FILES
    # ==========================================================

    def download_files(self, verified_data):
        order_id = verified_data.get("orderId")
        file_urls = verified_data.get("fileUrls", [])
        print_settings = verified_data.get("printSettings", {})

        if not order_id or not file_urls:
            print("❌ No files found in verification data")
            return []

        job_dir = os.path.join(self.base_dir, order_id)
        os.makedirs(job_dir, exist_ok=True)

        downloaded = []
        files_metadata = print_settings.get("files", [])

        for idx, url in enumerate(file_urls):
            try:
                filename = url.split("/")[-1].split("?")[0]
                if not filename.lower().endswith((".pdf", ".jpg", ".jpeg", ".png")):
                    filename = f"file_{idx+1}.pdf"

                local_path = os.path.join(job_dir, f"{idx}.pdf")

                print(f"⬇️ Downloading: {filename}")

                r = requests.get(url, timeout=20)
                r.raise_for_status()

                content = r.content

                if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    print("   🔄 Converting image to PDF...")
                    image = Image.open(io.BytesIO(content))
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(local_path, "PDF", resolution=100.0)
                else:
                    with open(local_path, "wb") as f:
                        f.write(content)

                file_settings = (
                    files_metadata[idx]
                    if idx < len(files_metadata)
                    else {}
                )

                downloaded.append(
                    {"path": local_path, "settings": file_settings}
                )

                print(f"✅ Saved: {local_path}")

            except Exception as e:
                print(f"❌ Failed downloading {url}: {e}")

        return downloaded

    # ==========================================================
    # MARK AS PRINTED
    # ==========================================================

    def mark_as_printed(self, order_id):
        url = f"{self.base_url}/mark-printed"
        headers = {"x-printer-key": self.printer_key}

        try:
            res = requests.post(
                url,
                json={"orderId": order_id},
                headers=headers,
                timeout=5
            )

            if res.status_code == 200:
                print(f"✅ Order {order_id} marked as printed")

                # 🧹 Cleanup local temp files
                job_dir = os.path.join(self.base_dir, order_id)
                if os.path.exists(job_dir):
                    shutil.rmtree(job_dir)

            else:
                print(f"⚠️ Failed to mark printed: {res.status_code}")

        except Exception as e:
            print(f"⚠️ Could not notify backend: {e}")
