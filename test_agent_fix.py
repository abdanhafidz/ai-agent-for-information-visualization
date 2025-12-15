import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_agent():
    print("1. Fetching Datasets...")
    try:
        r = requests.get(f"{BASE_URL}/datasets/?page_size=1")
        r.raise_for_status()
        data = r.json()
        datasets = data.get("founds", [])
        
        if not datasets:
            print("❌ No datasets found. Please upload a dataset first via the UI.")
            sys.exit(1)
            
        dataset_id = datasets[0]["id"]
        filename = datasets[0]["filename"]
        print(f"✅ Found Dataset: {dataset_id} ({filename})")
        
        print(f"\n2. Testing Agent Analyze on Dataset {dataset_id}...")
        payload = {
            "dataset_id": dataset_id,
            "prompt": "Show me a simple bar chart of the data"
        }
        
        # Increase timeout as agent might be slow
        r = requests.post(f"{BASE_URL}/agent/analyze", json=payload, timeout=60)
        
        try:
            r.raise_for_status()
            res_json = r.json()
            
            print("✅ Agent Response Received!")
            print(f"Explanation: {res_json.get('explanation')}")
            
            chart_config = res_json.get("chart_config")
            if chart_config and "data" in chart_config and "layout" in chart_config:
                print("✅ Chart Config is valid structure.")
            else:
                print(f"⚠️ Chart Config missing or invalid: {json.dumps(chart_config, indent=2)}")
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"Response Text: {r.text}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON Response: {r.text}")
            
    except Exception as e:
        print(f"❌ Execution Error: {e}")

if __name__ == "__main__":
    test_agent()
