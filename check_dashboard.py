import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def check_dashboard_data():
    try:
        print("Fetching all visualizations...")
        r = requests.get(f"{BASE_URL}/visualizations/")
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"Data received: {len(data)} items")
            if len(data) > 0:
                print("First item sample:", json.dumps(data[0], default=str)[:100])
            else:
                print("⚠️ List is empty!")
        else:
            print(f"❌ Error: {r.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    check_dashboard_data()
