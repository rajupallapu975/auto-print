import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import os


class FirebaseService:
    def __init__(self, key_path="serviceAccountKey.json"):
        if not os.path.exists(key_path):
            raise FileNotFoundError(
                f"❌ Firebase key file not found: {key_path}"
            )

        # Initialize only once
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
                print("🔥 Firebase initialized successfully")
            except Exception as e:
                raise RuntimeError(f"Firebase init failed: {e}")
        else:
            print("ℹ️ Firebase already initialized")

        self.db = firestore.client()

    # ==========================================================
    # GET ORDER BY PICKUP CODE
    # ==========================================================

    def get_order_by_pickup_code(self, pickup_code):
        try:
            code_str = str(pickup_code).strip()
            print(f"🔍 Searching for pickup code: {code_str}")

            # 1. Try searching by String
            query = (
                self.db.collection("orders")
                .where(filter=FieldFilter("pickupCode", "==", code_str))
                .limit(1)
                .stream()
            )
            docs = list(query)

            # 2. If not found and numeric, try searching by Integer
            if not docs and code_str.isdigit():
                print(f"   ℹ️ Not found as string, trying as integer...")
                query = (
                    self.db.collection("orders")
                    .where(filter=FieldFilter("pickupCode", "==", int(code_str)))
                    .limit(1)
                    .stream()
                )
                docs = list(query)

            if not docs:
                print(f"❌ No order found matching [{code_str}]")
                return {"success": False, "error": "ORDER_NOT_FOUND"}

            doc = docs[0]
            data = doc.to_dict()
            data["id"] = doc.id
            data["success"] = True

            print(f"✅ Order found: {doc.id}")
            return data

        except Exception as e:
            print(f"❌ Firestore query failed: {e}")
            return {"success": False, "error": "FIREBASE_ERROR", "message": str(e)}
