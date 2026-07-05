import requests
import os

def upload_to_terabox(file_path, ndus_cookies_str):
    # Convert cookie string to dict
    cookies = {}
    for item in ndus_cookies_str.split(';'):
        item = item.strip()
        if not item:
            continue
        key, value = item.split('=', 1)
        cookies[key] = value

    # Replace with actual Terabox upload endpoint
    # For demonstration, we'll use a placeholder.
    url = "https://www.terabox.com/upload"  # replace with actual API
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    files = {'file': open(file_path, 'rb')}
    # Many services expect a multipart form with certain fields.
    # Adjust according to your NDUS API.
    resp = requests.post(url, headers=headers, cookies=cookies, files=files)
    if resp.status_code == 200:
        # Assume response contains download URL
        data = resp.json()
        return data.get('download_url') or data.get('link')
    else:
        raise Exception(f"Upload failed: {resp.text}")