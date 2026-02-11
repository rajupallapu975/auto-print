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
            print(f"🔍 Searching for pickup code: {pickup_code}")

            query = (
                self.db.collection("orders")
                .where(filter=FieldFilter("pickupCode", "==", str(pickup_code)))
                .limit(1)
                .stream()
            )

            docs = list(query)

            if not docs:
                print("❌ No order found")
                return None

            doc = docs[0]
            data = doc.to_dict()
            data["id"] = doc.id

            print(f"✅ Order found: {doc.id}")
            return data

        except Exception as e:
            print(f"❌ Firestore query failed: {e}")
            return None
