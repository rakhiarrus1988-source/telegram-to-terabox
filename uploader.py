import os
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor

def check_ndus_token(ndus_token):
    """Checks if the NDUS token is valid and not expired."""
    print("🔍 Checking NDUS token validity...")
    url = "https://teraboxapp.com"
    headers = {"Cookie": f"ndus={ndus_token}", "User-Agent": "Mozilla/5.0..."}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        res_json = response.json()
        if res_json.get("errno") == 0:
            print(f"✅ Token Valid! User: {res_json.get('baidu_name')}")
            return True
        return False
    except: return False

def upload_to_terabox(file_path, ndus_token):
    """Fixed Speedy Uploader using Teraboxapp Endpoints."""
    if not check_ndus_token(ndus_token):
        raise Exception("❌ Invalid or Expired Token.")

    # [File detection and path logic here - omitted for brevity]
    # ... (Standard file handling) ...

    # Pre-create request
    url_precreate = "https://teraboxapp.com"
    headers = {"Cookie": f"ndus={ndus_token}", "User-Agent": "..."}
    params = {"method": "precreate", "app_id": "250528"}
    
    # ... (MD5 hashing and block list generation) ...
    # ... (Requests to precreate) ...

    # Multi-threaded Upload
    # ... (ThreadPoolExecutor for parallel uploads) ...

    # Finalize
    # ... (Final check_ndus_token/create call) ...
    print("🎉 Upload Completed Successfully!")
