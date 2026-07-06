import os
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor

# TeraBox ka standard block size (4MB) high speed upload ke liye
BLOCK_SIZE = 4 * 1024 * 1024 

def get_file_md5(file_path):
    """Puri file ka MD5 hash nikalne ke liye"""
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            md5.update(chunk)
    return md5.hexdigest()

def get_block_list(file_path):
    """File ke har 4MB chunk ka alag MD5 nikalne ke liye"""
    block_list = []
    with open(file_path, "rb") as f:
        while chunk := f.read(BLOCK_SIZE):
            block_list.append(hashlib.md5(chunk).hexdigest())
    return block_list

def upload_block_worker(ndus_token, upload_url, file_path, block_index):
    """Single block ko thread ke zariye speedy upload karne ka worker"""
    headers = {
        "Cookie": f"ndus={ndus_token}",
        "User-Agent": "Mozilla/5.0"
    }
    with open(file_path, "rb") as f:
        f.seek(block_index * BLOCK_SIZE)
        chunk = f.read(BLOCK_SIZE)
    
    files = {"file": chunk}
    response = requests.post(upload_url, headers=headers, files=files)
    return response.status_code == 200

def upload_to_terabox_speedy(file_path, ndus_token, remote_dir="/"):
    # --- AUTOMATIC SIMPLIFIED RENAMING SYSTEM ---
    # File ki original extension check karega (.mp4, .mkv etc.)
    _, file_extension = os.path.splitext(file_path)
    if not file_extension:
        file_extension = ".dat"
        
    # Cloud par automatic simple language name save hoga (e.g., 1.mkv)
    target_file_name = f"1{file_extension}" 
    file_size = os.path.getsize(file_path)
    
    print(f"📦 Original Local File: {os.path.basename(file_path)}")
    print(f"🔄 Saving on Cloud as: {target_file_name}")
    print("⏳ File hashes processing...")
    
    file_md5 = get_file_md5(file_path)
    block_list = get_block_list(file_path)
    
    headers = {
        "Cookie": f"ndus={ndus_token}",
        "User-Agent": "Mozilla/5.0"
    }
    
    # STEP 1: Pre-create Request (🎯 1024terabox URL based)
    print("🔄 Initializing pre-create on 1024terabox...")
    precreate_url = "https://1024terabox.com"
    data = {
        "path": os.path.join(remote_dir, target_file_name),
        "size": str(file_size),
        "isdir": "0",
        "block_list": str(block_list).replace("'", '"'),
        "method": "precreate"
    }
    
    res = requests.post(precreate_url, headers=headers, data=data).json()
    
    if res.get("errno") != 0:
        raise Exception(f"Pre-create failed: {res}")
        
    # Agar file cloud par pehle se maujood hai (Instant Rapid Upload)
    if res.get("return_type") == 2:
        print("⚡ Instant Upload Success! Data save ho gaya bina upload kiye.")
        return f"https://1024terabox.com{remote_dir}"

    uploadid = res["uploadid"]
    block_urls = res["block_list"]
    
    # STEP 2: Parallel Multi-threaded Uploading
    print(f"🚀 Speedy Upload Starting: {len(block_list)} blocks parallelly ja rahe hain...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for index, block_id in enumerate(block_urls):
            # Core storage cluster URL mapping
            upload_url = f"https://baidu.com{uploadid}&partseq={index}"
            futures.append(executor.submit(upload_block_worker, ndus_token, upload_url, file_path, index))
            
        results = [f.result() for f in futures]
        
    if not all(results):
        raise Exception("❌ Kuch chunks upload nahi ho paaye. Check network connection.")

    # STEP 3: Create File Finalize (🎯 1024terabox URL based)
    print("🏁 Upload done. Finalizing file chunks...")
    create_url = "https://1024terabox.com"
    create_data = {
        "path": os.path.join(remote_dir, target_file_name),
        "size": str(file_size),
        "isdir": "0",
        "block_list": str(block_list).replace("'", '"'),
        "uploadid": uploadid,
        "method": "create"
    }
    
    final_res = requests.post(create_url, headers=headers, data=create_data).json()
    
    if final_res.get("errno") == 0:
        print(f"🎉 File successfully uploaded as '{target_file_name}'!")
        return f"https://1024terabox.com{remote_dir}"
    else:
        raise Exception(f"Final file creation failed: {final_res}")

# --- Execution Block ---
if __name__ == "__main__":
    # 🔥 Yahan apna 1024terabox se nikala hua real ndus token dalein
    TOKEN = "YOUR_1024TERABOX_NDUS_TOKEN"  
    
    # 🔥 Aapki kisi bhi folder ya bade naam wali file ka path
    FILE = "bade_naam_wali_movie_file.mkv"  
    
    try:
        dashboard_link = upload_to_terabox_speedy(FILE, TOKEN)
        print(f"🔗 1024TeraBox Link: {dashboard_link}")
    except Exception as e:
        print(f"❌ Error Occurred: {e}")
