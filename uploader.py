import os
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor

def upload_to_terabox(file_path, ndus_token):
    """
    Colab Automated System ke liye optimized speedy uploader.
    """
    # 🤖 AUTO-DETECT DOWNLOADED FILE: Agar path empty hai ya valid nahi hai
    if not file_path or not os.path.exists(file_path):
        # Colab environment se downloaded files filter karega
        files = [f for f in os.listdir('.') if os.path.isfile(f) and f not in ['uploader.py', '.config']]
        if files:
            # Sabse latest file ko select karega
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            file_path = files[0]
            print(f"📦 Colab Auto-Detect: Uploading latest file -> {file_path}")
        else:
            raise Exception("❌ Error: Colab par koi downloaded file nahi mili!")

    BLOCK_SIZE = 4 * 1024 * 1024  # 4MB blocks standard
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    remote_dir = "/"

    # --- 1. HASH CALCULATION ---
    print("⏳ File chunks aur MD5 calculate ho rahe hain...")
    md5_obj = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            md5_obj.update(chunk)
    file_md5 = md5_obj.hexdigest()

    block_list = []
    with open(file_path, "rb") as f:
        while chunk := f.read(BLOCK_SIZE):
            block_list.append(hashlib.md5(chunk).hexdigest())

    # --- 2. PRE-CREATE REQUEST WITH APP_ID ---
    print("🔄 TeraBox Pre-create request initiated...")
    
    # 🌟 CRITICAL FIX: TeraBox xpan API endpoint with official App ID
    url_precreate = "https://terabox.com"
    
    headers = {
        "Cookie": f"ndus={ndus_token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    data_precreate = {
        "path": f"/{file_name}",
        "size": str(file_size),
        "isdir": "0",
        "block_list": str(block_list).replace("'", '"'),
        "autoinit": "1"
    }
    
    response = requests.post(url_precreate, headers=headers, data=data_precreate)
    
    # Error safe-guarding if server sends HTML instead of JSON
    try:
        res_data = response.json()
    except Exception:
        print(f"❌ Server response JSON nahi hai! Status Code: {response.status_code}")
        print(f"📄 Server Response Snippet: {response.text[:300]}")
        raise Exception("TeraBox ne request block kar di. Apna ndus token check karein ki woh active hai ya expire.")

    if res_data.get("errno") != 0:
        raise Exception(f"Pre-create failed. TeraBox Error Code: {res_data.get('errno')}")

    # Instant Upload logic (Server par file already hai toh zero data download)
    if res_data.get("return_type") == 2:
        print("⚡ Instant Upload Success! (File pehle se server par thi)")
        return f"https://terabox.com{remote_dir}"

    uploadid = res_data["uploadid"]
    block_urls = res_data["block_list"]

    # --- 3. MULTI-THREADED SPEEDY UPLOAD ---
    def worker(index):
        with open(file_path, "rb") as f:
            f.seek(index * BLOCK_SIZE)
            chunk_data = f.read(BLOCK_SIZE)
        
        target_url = f"https://baidu.com{uploadid}&partseq={index}"
        res = requests.post(target_url, headers=headers, files={"file": chunk_data})
        return res.status_code == 200

    print(f"🚀 Speedy Upload Starting: {len(block_list)} pieces ek saath upload ho rahe hain...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker, idx) for idx in range(len(block_list))]
        results = [f.result() for f in futures]

    if not all(results):
        raise Exception("❌ Kuch chunks crash ho gaye. Parallel uploading failed.")

    # --- 4. FINALIZE FILE ---
    print("🏁 Finalizing file on TeraBox...")
    url_create = "https://terabox.com"
    
    data_create = {
        "path": f"/{file_name}",
        "size": str(file_size),
        "isdir": "0",
        "block_list": str(block_list).replace("'", '"'),
        "uploadid": uploadid
    }
    
    final_response = requests.post(url_create, headers=headers, data=data_create).json()
    
    if final_response.get("errno") == 0:
        print("🎉 Speedy Upload Completed Successfully!")
        return f"https://terabox.com{remote_dir}"
    else:
        raise Exception(f"Finalization failed code: {final_response.get('errno')}")
