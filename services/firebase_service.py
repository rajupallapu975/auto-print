import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import os

class FirebaseService:
    def __init__(self, key_path='serviceAccountKey.json'):
        if not os.path.exists(key_path):
            raise FileNotFoundError("❌ serviceAccountKey.json not found")

        try:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
        except ValueError:
            pass

        self.db = firestore.client()

    def get_order_by_pickup_code(self, pickup_code):
        print(f"🔍 Searching for pickup code: {pickup_code}...")
        query = (
            self.db.collection("orders")
            .where(filter=FieldFilter("pickupCode", "==", str(pickup_code)))
            .limit(1)
            .stream()
        )

        for doc in query:
            data = doc.to_dict()
            data["id"] = doc.id
            print(f"✅ Order found! Order ID: {doc.id}")
            return data

        print("❌ No order found")
        return None
