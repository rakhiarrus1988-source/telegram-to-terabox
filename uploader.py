import os
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor

def upload_to_terabox(file_path, ndus_token):
    """
    NDUS token ke saath file upload karega speed ke saath.
    Aapke automated system ka exact same format aur structure.
    """
    # 🤖 AUTO-DETECT: Agar Colab me file path automatic check karna ho
    if not file_path or not os.path.exists(file_path):
        # Colab ki current directory me se sabse latest ya standard file dhundega
        files = [f for f in os.listdir('.') if os.path.isfile(f) and f != 'uploader.py']
        if files:
            file_path = files[0] # Jo file download hui hai usko auto-select karega
            print(f"📦 Automated System ne file detect ki: {file_path}")
        else:
            raise Exception("❌ Colab par koi downloaded file nahi mili!")

    # Speed ke liye constants (4MB blocks)
    BLOCK_SIZE = 4 * 1024 * 1024
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    remote_dir = "/"

    # --- BLOCK 1: HASH CALCULATIONS ---
    print("⏳ File chunks calculate ho rahe hain...")
    # Full File MD5
    md5_obj = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            md5_obj.update(chunk)
    file_md5 = md5_obj.hexdigest()

    # Split Blocks MD5
    block_list = []
    with open(file_path, "rb") as f:
        while chunk := f.read(BLOCK_SIZE):
            block_list.append(hashlib.md5(chunk).hexdigest())

    # --- BLOCK 2: PRE-CREATE REQUEST ---
    print("🔄 TeraBox Pre-create request initiated...")
    url_precreate = "https://terabox.com"
    headers = {"Cookie": f"ndus={ndus_token}", "User-Agent": "Mozilla/5.0"}
    
    data_precreate = {
        "path": os.path.join(remote_dir, file_name),
        "size": str(file_size),
        "isdir": "0",
        "block_list": str(block_list).replace("'", '"'),
        "method": "precreate"
    }
    
    response = requests.post(url_precreate, headers=headers, data=data_precreate)
    
    # Method fail-safe check jaisa aapke original code me tha
    if response.status_code != 200:
        print("⚠️ Direct cookie method failed. Trying fallback authorization header...")
        headers_fallback = {"Authorization": f"Bearer {ndus_token}", "User-Agent": "Mozilla/5.0"}
        response = requests.post(url_precreate, headers=headers_fallback, data=data_precreate)

    res_data = response.json()
    if res_data.get("errno") != 0:
        raise Exception(f"Pre-create failed. Error Code: {res_data.get('errno')}")

    # Instant Upload: Agar server pe file pehle se hogi toh turant link dega
    if res_data.get("return_type") == 2:
        print("⚡ Instant Speedy Upload Success!")
        return f"https://terabox.com{remote_dir}"

    uploadid = res_data["uploadid"]
    block_urls = res_data["block_list"]

    # --- BLOCK 3: MULTI-THREADED SPEEDY UPLOAD WORKER ---
    def worker(index, upload_target_url):
        with open(file_path, "rb") as f:
            f.seek(index * BLOCK_SIZE)
            chunk_data = f.read(BLOCK_SIZE)
        res = requests.post(upload_target_url, headers=headers, files={"file": chunk_data})
        return res.status_code == 200

    print(f"🚀 Speedy Upload Starting: {len(block_list)} blocks parallelly ja rahe hain...")
    
    # Threads aapki speed max kar denge (Colab network ka full use)
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for index, _ in enumerate(block_urls):
            target_url = f"https://baidu.com{uploadid}&partseq={index}"
            futures.append(executor.submit(worker, index, target_url))
        
        results = [f.result() for f in futures]

    if not all(results):
        raise Exception("❌ Kuch chunks crash ho gaye. File upload incomplete.")

    # --- BLOCK 4: FINALIZE / CREATE ---
    print("🏁 Finalizing file on TeraBox...")
    url_create = "https://terabox.com"
    data_create = {
        "path": os.path.join(remote_dir, file_name),
        "size": str(file_size),
        "isdir": "0",
        "block_list": str(block_list).replace("'", '"'),
        "uploadid": uploadid,
        "method": "create"
    }
    
    final_response = requests.post(url_create, headers=headers, data=data_create).json()
    
    if final_response.get("errno") == 0:
        print("🎉 Speedy Upload Complete successfully!")
        return f"https://terabox.com{remote_dir}"
    else:
        raise Exception(f"Finalization failed code: {final_response.get('errno')}")
