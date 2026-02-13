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
        """Verify the pickup code with the backend."""
        url = f"{self.base_url}/verify-pickup-code"
        headers = {"x-printer-key": self.printer_key}
        
        # Strip whitespace from code
        code = str(pickup_code).strip()

        print(f"📡 Verifying code: [{code}]")

        for attempt in range(self.max_retries + 1):
            try:
                # Try as JSON payload
                payload = {"pickupCode": code}
                res = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=15
                )

                if res.status_code == 400:
                    try:
                        data = res.json()
                        error_msg = data.get("message") or data.get("error") or "Order not printable"
                        print(f"⚠️ Backend rejected (400): {error_msg}")
                        return {"success": False, "error": error_msg}
                    except ValueError:
                        print("⚠️ Backend returned 400 but no JSON")
                        return {"success": False, "error": "Invalid Request"}

                if res.status_code == 403:
                    print("❌ Auth Error: Check your x-printer-key")
                    return {"success": False, "error": "AUTH_ERROR"}

                if res.status_code == 404:
                    print(f"❌ Backend returned 404 for code {code}")
                    return {"success": False, "error": "INVALID_CODE"}

                # For other errors, log the response body to help debugging
                if not res.ok:
                    print(f"⚠️ Backend error ({res.status_code}): {res.text[:200]}")
                    res.raise_for_status()

                data = res.json()

                if not data.get("success", False):
                    backend_msg = data.get("message") or data.get("error") or "Unknown error"
                    print(f"⚠️ Backend rejected code: {backend_msg}")
                    return {"success": False, "error": backend_msg}

                # Success!
                print(f"✅ Backend reached successfully.")
                print(f"✅ Order {data.get('orderId')} status: READY TO PRINT")
                return data

            except requests.exceptions.Timeout:
                print(f"⏳ Timeout on attempt {attempt+1}")
                if attempt == self.max_retries:
                    return {"success": False, "error": "TIMEOUT"}
                time.sleep(1)

            except requests.exceptions.ConnectionError:
                print(f"📡 Connection error on attempt {attempt+1}")
                if attempt == self.max_retries:
                    return {"success": False, "error": "IP_ERROR"}
                time.sleep(2)

            except Exception as e:
                print(f"❌ Unexpected error in verify_code: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": "SYSTEM_ERROR", "details": str(e)}

        return {"success": False, "error": "IP_ERROR"}

    # ==========================================================
    # DOWNLOAD FILES
    # ==========================================================

    def download_files(self, verified_data):
        order_id = verified_data.get("orderId")
        
        # Support both 'fileUrls' (legacy) and 'files' (new structure)
        file_urls = verified_data.get("fileUrls", [])
        if not file_urls and "files" in verified_data:
            # If 'files' is a list of objects, extract 'url' from each
            files_raw = verified_data.get("files", [])
            if isinstance(files_raw, list):
                if files_raw and isinstance(files_raw[0], dict):
                    file_urls = [f.get("url") for f in files_raw if f.get("url")]
                else:
                    file_urls = files_raw # It's already a list of strings

        print_settings = verified_data.get("printSettings", {})

        if not order_id or not file_urls:
            print(f"❌ No files found for order {order_id}")
            return {"success": False, "error": "MISSING_FILES"}

        job_dir = os.path.join(self.base_dir, order_id)
        os.makedirs(job_dir, exist_ok=True)

        downloaded = []
        errors = []
        files_metadata = print_settings.get("files", [])

        for idx, url in enumerate(file_urls):
            if not url: continue
            try:
                is_cloudinary = "cloudinary" in url.lower()
                
                # Try to determine if it's an image from URL or metadata
                is_image_ext = url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png"))
                
                local_path = os.path.join(job_dir, f"{idx}.pdf")

                print(f"⬇️ Downloading{' (Cloudinary)' if is_cloudinary else ''}: {url.split('/')[-1][:20]}...")

                r = requests.get(url, timeout=25)
                r.raise_for_status()

                content = r.content
                content_type = r.headers.get("Content-Type", "").lower()
                
                # Final check if it's an image (either by extension or mime type)
                is_actually_image = is_image_ext or "image" in content_type

                if is_actually_image:
                    print("   🔄 Converting image to PDF...")
                    try:
                        image = Image.open(io.BytesIO(content))
                        if image.mode in ("RGBA", "P"):
                            image = image.convert("RGB")
                        image.save(local_path, "PDF", resolution=100.0)
                    except Exception as img_err:
                        print(f"   ⚠️ PIL failed to process image: {img_err}. Saving raw.")
                        with open(local_path, "wb") as f:
                            f.write(content)
                else:
                    with open(local_path, "wb") as f:
                        f.write(content)

                # Try to get individual file settings
                # 1. From printSettings.files[idx]
                # 2. From verified_data.files[idx] (if it was a list of objects)
                file_settings = {}
                if idx < len(files_metadata):
                    file_settings = files_metadata[idx]
                elif "files" in verified_data and isinstance(verified_data["files"], list) and idx < len(verified_data["files"]):
                    raw_item = verified_data["files"][idx]
                    if isinstance(raw_item, dict):
                        file_settings = raw_item

                downloaded.append(
                    {"path": local_path, "settings": file_settings}
                )

                print(f"✅ Saved: {local_path}")

            except Exception as e:
                error_type = "CLOUDINARY_ERROR" if "cloudinary" in url.lower() else "DOWNLOAD_ERROR"
                print(f"❌ Failed downloading {url}: {e}")
                errors.append({"url": url, "error": str(e), "type": error_type})

        if not downloaded and errors:
            return {"success": False, "error": errors[0]["type"], "details": errors}

        return {"success": True, "files": downloaded, "errors": errors}

    # ==========================================================
    # REPORT ISSUE
    # ==========================================================

    def report_issue(self, order_id, issue_type, details):
        url = f"{self.base_url}/report-issue"
        headers = {"x-printer-key": self.printer_key}

        try:
            res = requests.post(
                url,
                json={
                    "orderId": order_id,
                    "issueType": issue_type,
                    "details": details
                },
                headers=headers,
                timeout=5
            )
            return res.status_code == 200
        except Exception as e:
            print(f"⚠️ Could not report issue: {e}")
            return False

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
