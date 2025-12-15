import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def check_api():
    print("Checking API Health...")
    try:
        # Check Datasets
        r = requests.get(f"{BASE_URL}/datasets/?page_size=1")
        if r.status_code == 200:
            print("✅ GET /datasets: OK")
        else:
            print(f"❌ GET /datasets: {r.status_code}")

        # Check Visualizations (List) - New Endpoint
        # We assume dataset ID 1 exists or return empty list is fine for 200 OK
        r = requests.get(f"{BASE_URL}/visualizations/dataset/99999") 
        if r.status_code == 200:
            print("✅ GET /visualizations/dataset/{id}: OK (Empty list expected)")
        else:
            print(f"❌ GET /visualizations/dataset/{id}: {r.status_code} - {r.text}")

        # Check Visualizations (All)
        r = requests.get(f"{BASE_URL}/visualizations/")
        if r.status_code == 200:
            print("✅ GET /visualizations/: OK")
        else:
            print(f"❌ GET /visualizations/: {r.status_code}")

    except Exception as e:
        print(f"❌ API Verification Failed: {e}")

if __name__ == "__main__":
    check_api()
