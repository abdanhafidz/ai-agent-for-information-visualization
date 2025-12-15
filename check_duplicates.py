import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def check_duplicates():
    try:
        r = requests.get(f"{BASE_URL}/visualizations/")
        if r.status_code == 200:
            data = r.json()
            print(f"Total Visualizations: {len(data)}")
            ids = [item['id'] for item in data]
            prompts = [item['prompt'] for item in data]
            
            print(f"IDs: {ids}")
            from collections import Counter
            print(f"Prompt Counts: {Counter(prompts)}")
        else:
            print(f"Error: {r.text}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_duplicates()
