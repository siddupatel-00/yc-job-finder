import os
import sys
import json
import requests

def load_env_file(filepath=".env"):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'").strip('"')

def main():
    load_env_file()

    api_token = os.environ.get("BRIGHT_DATA_API_TOKEN", "")
    collector_id = os.environ.get("BRIGHT_DATA_COLLECTOR_ID", "c_mt5wl2m71k9t9f0bwj")

    if not api_token:
        print("[ERROR] BRIGHT_DATA_API_TOKEN is missing or not configured in .env")
        sys.exit(1)

    url = f"https://api.brightdata.com/dca/trigger?collector={collector_id}&queue_next=1"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    payload = [{"url": "https://www.ycombinator.com/jobs"}]

    print(f"[*] Testing connection to Bright Data DCA API...")
    print(f"[*] Collector ID: {collector_id}")
    print(f"[*] Target Endpoint: {url}")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code in [200, 202]:
            print(f"[SUCCESS] Authenticated & Connected to Bright Data (HTTP {response.status_code})")
            try:
                data = response.json()
                print(f"[SUCCESS] Response Payload: {json.dumps(data, indent=2)}")
            except Exception:
                print(f"[SUCCESS] Response Text: {response.text}")
        elif response.status_code in [401, 403]:
            print(f"[ERROR] Invalid token or unauthorized collector ID (HTTP {response.status_code})")
            print(f"Response: {response.text}")
        else:
            print(f"[WARNING] Server returned status {response.status_code}: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network / Connection Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
