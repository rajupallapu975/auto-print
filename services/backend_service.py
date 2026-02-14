# ============================================================================
# AUTO-PRINT RASPBERRY PI CLIENT
# ============================================================================
# This script runs on the Raspberry Pi and handles:
# 1. Reading 6-digit codes from Arduino keypad
# 2. Verifying codes with the backend server
# 3. Downloading files from Cloudinary
# 4. Printing documents
# 5. Marking orders as completed
# ============================================================================

import requests
import os
from PIL import Image
import io
import shutil
import time

# ============================================================================
# BACKEND SERVICE CLASS
# ============================================================================
class BackendService:
    """
    Handles all communication with the backend server.
    Downloads files from Cloudinary URLs provided by the backend.
    """
    
    def __init__(
        self,
        base_url="https://printer-backend-ch2e.onrender.com",
        base_dir="temp_jobs",
        printer_key="LOCAL_PRINTER",
        max_retries=2
    ):
        self.base_url = base_url.rstrip("/")
        self.base_dir = base_dir
        self.printer_key = printer_key
        self.max_retries = max_retries
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
    
    # ========================================================================
    # VERIFY PICKUP CODE
    # ========================================================================
    def verify_code(self, pickup_code):
        """
        Verify the pickup code with the backend server.
        
        Args:
            pickup_code (str): 6-digit pickup code
            
        Returns:
            dict: Response with success status and order details
        """
        url = f"{self.base_url}/verify-pickup-code"
        headers = {"x-printer-key": self.printer_key}
        
        # Clean the code
        code = str(pickup_code).strip()
        
        print(f"📡 Verifying code: [{code}]")
        
        for attempt in range(self.max_retries + 1):
            try:
                # Send verification request
                payload = {"pickupCode": code}
                res = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=15
                )
                
                # Handle different status codes
                if res.status_code == 400:
                    data = res.json()
                    error_msg = data.get("error", "Order not printable")
                    print(f"⚠️ Backend rejected (400): {error_msg}")
                    return {"success": False, "error": error_msg}
                
                if res.status_code == 404:
                    print(f"❌ Invalid or expired code: {code}")
                    return {"success": False, "error": "INVALID_CODE"}
                
                if res.status_code == 403:
                    print("❌ Auth Error: Check your x-printer-key")
                    return {"success": False, "error": "AUTH_ERROR"}
                
                # Raise for other HTTP errors
                if not res.ok:
                    print(f"⚠️ Backend error ({res.status_code}): {res.text[:200]}")
                    res.raise_for_status()
                
                # Parse successful response
                data = res.json()
                
                if not data.get("success", False):
                    error_msg = data.get("error", "Unknown error")
                    print(f"⚠️ Backend rejected code: {error_msg}")
                    return {"success": False, "error": error_msg}
                
                # Success!
                print(f"✅ Code verified successfully")
                print(f"✅ Order {data.get('orderId')} ready to print")
                return data
            
            except requests.exceptions.Timeout:
                print(f"⏳ Timeout on attempt {attempt + 1}")
                if attempt == self.max_retries:
                    return {"success": False, "error": "TIMEOUT"}
                time.sleep(1)
            
            except requests.exceptions.ConnectionError:
                print(f"📡 Connection error on attempt {attempt + 1}")
                if attempt == self.max_retries:
                    return {"success": False, "error": "CONNECTION_ERROR"}
                time.sleep(2)
            
            except Exception as e:
                print(f"❌ Unexpected error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": "SYSTEM_ERROR", "details": str(e)}
        
        return {"success": False, "error": "CONNECTION_ERROR"}
    
    # ========================================================================
    # DOWNLOAD FILES FROM CLOUDINARY
    # ========================================================================
    def download_files(self, verified_data):
        """
        Download files from Cloudinary URLs.
        Converts images to PDF if necessary.
        
        Args:
            verified_data (dict): Response from verify_code()
            
        Returns:
            dict: Download results with file paths
        """
        order_id = verified_data.get("orderId")
        file_urls = verified_data.get("fileUrls", [])
        print_settings = verified_data.get("printSettings", {})
        
        if not order_id or not file_urls:
            print(f"❌ No files found for order {order_id}")
            return {"success": False, "error": "MISSING_FILES"}
        
        # Create job directory
        job_dir = os.path.join(self.base_dir, order_id)
        os.makedirs(job_dir, exist_ok=True)
        
        downloaded = []
        errors = []
        
        print(f"📥 Downloading {len(file_urls)} file(s)...")
        
        for idx, url in enumerate(file_urls):
            if not url:
                continue
            
            try:
                # Determine if it's a Cloudinary URL
                is_cloudinary = "cloudinary" in url.lower()
                
                # Check if it's an image
                is_image_ext = url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png"))
                
                local_path = os.path.join(job_dir, f"file_{idx}.pdf")
                
                print(f"⬇️  [{idx + 1}/{len(file_urls)}] Downloading{' (Cloudinary)' if is_cloudinary else ''}...")
                
                # Download file
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                
                content = r.content
                content_type = r.headers.get("Content-Type", "").lower()
                
                # Check if it's actually an image
                is_actually_image = is_image_ext or "image" in content_type
                
                if is_actually_image:
                    print("   🔄 Converting image to PDF...")
                    try:
                        # Convert image to PDF
                        image = Image.open(io.BytesIO(content))
                        if image.mode in ("RGBA", "P"):
                            image = image.convert("RGB")
                        image.save(local_path, "PDF", resolution=100.0)
                    except Exception as img_err:
                        print(f"   ⚠️  Image conversion failed: {img_err}")
                        # Save as raw file
                        with open(local_path, "wb") as f:
                            f.write(content)
                else:
                    # Save PDF directly
                    with open(local_path, "wb") as f:
                        f.write(content)
                
                downloaded.append({"path": local_path})
                print(f"   ✅ Saved: {local_path}")
            
            except Exception as e:
                error_type = "CLOUDINARY_ERROR" if "cloudinary" in url.lower() else "DOWNLOAD_ERROR"
                print(f"   ❌ Failed: {e}")
                errors.append({"url": url, "error": str(e), "type": error_type})
        
        if not downloaded and errors:
            return {"success": False, "error": errors[0]["type"], "details": errors}
        
        print(f"✅ Downloaded {len(downloaded)} file(s) successfully")
        return {"success": True, "files": downloaded, "errors": errors}
    
    # ========================================================================
    # MARK ORDER AS PRINTED
    # ========================================================================
    def mark_as_printed(self, order_id):
        """
        Notify the backend that printing is complete.
        This revokes the pickup code.
        
        Args:
            order_id (str): Order ID to mark as printed
        """
        url = f"{self.base_url}/mark-printed"
        headers = {"x-printer-key": self.printer_key}
        
        try:
            res = requests.post(
                url,
                json={"orderId": order_id},
                headers=headers,
                timeout=10
            )
            
            if res.status_code == 200:
                print(f"✅ Order {order_id} marked as printed")
                
                # Clean up temp files
                job_dir = os.path.join(self.base_dir, order_id)
                if os.path.exists(job_dir):
                    shutil.rmtree(job_dir)
                    print(f"🧹 Cleaned up temp files")
            else:
                print(f"⚠️  Failed to mark printed: {res.status_code}")
        
        except Exception as e:
            print(f"⚠️  Could not notify backend: {e}")
