import os
import sys

# Ensure services are importable
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.firebase_service import FirebaseService

def check_order(code):
    print(f"\nScanning Firebase for code: {code}")
    print("-" * 30)

    try:
        # Initialize Firebase
        fb = FirebaseService()
        
        # Search
        order = fb.get_order_by_pickup_code(code)

        if not order.get("success"):
            print(f"❌ Order NOT FOUND: {order.get('error')}")
            print(f"   Reason: The code [{code}] does not exist in 'orders' collection.")
            return

        print(f"✅ ORDER EXISTS!")
        print(f"   Order ID: {order.get('id')}")
        print(f"   Status: {order.get('printStatus')}")
        print(f"   Created At: {order.get('createdAt')}")
        
        files = order.get('fileUrls') or order.get('files') or []
        print(f"   Files: {len(files)} file(s)")
        
        if order.get('printStatus') == 'PRINTED':
            print("\n⚠️ Note: Status is 'PRINTED'. If using old backend, this will be rejected.")
        
    except Exception as e:
        print(f"❌ Error connecting to Firebase: {e}")
        print("   Check if 'serviceAccountKey.json' is in this folder.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        code = sys.argv[1]
    else:
        code = input("Enter Pickup Code to Check: ")
    
    check_order(code)
