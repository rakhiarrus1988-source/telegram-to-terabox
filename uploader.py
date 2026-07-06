
import os
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor

def upload_to_terabox(file_path, ndus_token):
    """
    TeraBox Official Global API endpoints ke saath fixed speedy uploader.
    """
    # 🤖 Auto-detect file if path is broken
    if not file_path or not os.path.exists(file_path):
        files = [f for f in os.listdir('.') if os.path.isfile(f) and f not in ['uploader.py', '.config']]
        if files:
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            file_path = files[0]
            print(f"📦 Colab Auto-Detect: Uploading latest file -> {file_path}")
        else:
            raise Exception("❌ Error: Colab par koi downloaded file nahi mili!")

    BLOCK_SIZE = 4 * 1024 * 1024  # 4MB Chunks
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

    # --- 2. PRE-CREATE REQUEST (GLOBAL API ENDPOINT) ---
    print("🔄 TeraBox Pre-create request initiated...")
    
    # 🔥 FIX: www.terabox.com ki jagah api.terabox.com secure global API use kar rahe hain
    url_precreate = "https://api.terabox.com/rest/2.0/xpan/file"
    
    headers = {
        "Cookie": f"ndus={ndus_token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }
    
    # Query parameters jisse cloudflare ya robot check bypass ho jaye
    params_precreate = {
        "method": "precreate",
        "app_id": "250528"
    }
    
    data_precreate = {
        "path": f"/{file_name}",
        "size": str(file_size),
        "isdir": "0",
        "block_list": str(block_list).replace("'", '"'),
        "autoinit": "1"
    }
    
    response = requests.post(url_precreate, headers=headers, params=params_precreate, data=data_precreate)
    
    try:
        res_data = response.json()
    except Exception:
        print(f"❌ Server response abhi bhi JSON nahi hai! Status Code: {response.status_code}")
        print(f"📄 Response Snippet: {response.text[:200]}")
        raise Exception("TeraBox API block issues. Apna ndus token refresh karein browser me login karke.")

    if res_data.get("errno") != 0:
        raise Exception(f"Pre-create failed. TeraBox Error Code: {res_data.get('errno')} | Msg: {res_data.get('show_msg')}")

    # Instant Upload logic (Zero data transfer agar server par file exist karti hai)
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
        
        # PCS upload node link
        target_url = f"https://baidu.com{uploadid}&partseq={index}"
        res = requests.post(target_url, headers=headers, files={"file": chunk_data})
        return res.status_code == 200

    print(f"🚀 Speedy Upload Starting: {len(block_list)} pieces parallelly upload ho rahe hain...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker, idx) for idx in range(len(block_list))]
        results = [f.result() for f in futures]

    if not all(results):
        raise Exception("❌ Kuch chunks crash ho gaye. Parallel uploading failed.")

    # --- 4. FINALIZE FILE ---
    print("🏁 Finalizing file on TeraBox...")
    url_create = "https://api.terabox.com/rest/2.0/xpan/file"
    
    params_create = {
        "method": "create",
        "app_id": "250528"
    }
    
    data_create = {
        "path": f"/{file_name}",
        "size": str(file_size),
        "isdir": "0",
        "block_list": str(block_list).replace("'", '"'),
        "uploadid": uploadid
    }
    
    final_response = requests.post(url_create, headers=headers, params=params_create, data=data_create).json()
    
    if final_response.get("errno") == 0:
        print("🎉 Speedy Upload Completed Successfully!")
        return f"https://terabox.com{remote_dir}"
    else:
        raise Exception(f"Finalization failed code: {final_response.get('errno')}")
