import requests
import os

def upload_to_terabox(file_path, ndus_token):
    """
    NDUS token ke through file upload karega.
    Agar aapka API Bearer token expect karta hai toh 'Authorization' header,
    Agar form-data mein token bhejna hai toh 'data' parameter use karein.
    """
    # 🔥 NOTE: Neeche diye gaye URL aur method ko apne actual NDUS API ke hisaab se change karein.
    # Yeh sirf example hai.
    url = "https://api.ndus.cloud/upload"  # ✅ YAHAN APNI REAL API URL DAALEIN
    
    headers = {
        "Authorization": f"Bearer {ndus_token}",  # Agar token header mein jaata hai
        "User-Agent": "Mozilla/5.0"
    }
    # Agar token form-data mein jaata hai toh neeche waala use karein:
    # data = {"token": ndus_token}
    # response = requests.post(url, headers=headers, data=data, files={'file': open(file_path, 'rb')})
    
    files = {'file': open(file_path, 'rb')}
    response = requests.post(url, headers=headers, files=files)
    
    if response.status_code == 200:
        try:
            data = response.json()
            # Maan liya ki response mein 'download_url' ya 'link' aata hai
            return data.get('download_url') or data.get('link') or "Upload success, but no link in response."
        except:
            return f"Uploaded successfully. Response: {response.text[:200]}"
    else:
        raise Exception(f"Upload fail: {response.status_code} - {response.text}")