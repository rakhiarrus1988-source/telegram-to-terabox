import asyncio
import os
from pyrogram import Client
from pyrogram.errors import RPCError
from config import get_credentials, mount_drive, get_session_path
from downloader import download_telegram_file
from uploader import upload_to_terabox

async def search_file_in_saved_messages(client, filename):
    """Saved Messages (me) mein file name search karega"""
    print("🔍 Saved Messages mein search ho raha hai...")
    saved_messages = await client.get_messages('me', limit=2000)  # limit badha sakte ho
    for msg in saved_messages:
        if msg.document and msg.document.file_name and filename.lower() in msg.document.file_name.lower():
            return msg.document.file_id, msg.document.file_name, msg.document.file_size
        elif msg.video and msg.video.file_name and filename.lower() in msg.video.file_name.lower():
            return msg.video.file_id, msg.video.file_name, msg.video.file_size
        elif msg.audio and msg.audio.file_name and filename.lower() in msg.audio.file_name.lower():
            return msg.audio.file_id, msg.audio.file_name, msg.audio.file_size
    return None, None, None

async def main():
    # 1️⃣ Drive Mount (Colab apne aap link dega)
    mount_drive()
    
    # 2️⃣ Credentials Load (Pehli baar maangega, fir save karega)
    creds = get_credentials()
    
    # 3️⃣ Pyrogram Client (Session Drive mein save hogi)
    session_path = get_session_path()
    client = Client(
        session_path,
        api_id=int(creds['api_id']),
        api_hash=creds['api_hash'],
        phone_number=creds['phone']
    )
    
    # 4️⃣ Login (Pehli baar OTP maangega, baad mein auto-login)
    try:
        await client.start()
        print("✅ Telegram Login Successful!")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return
    
    # 5️⃣ User se file name lo
    filename = input("\n📁 Saved Messages mein jis file ko download karna hai uska naam (ya part) likho: ").strip()
    if not filename:
        print("❌ Kuch likha hi nahi! Exiting.")
        return
    
    # 6️⃣ Search karo
    file_id, name, size = await search_file_in_saved_messages(client, filename)
    if file_id is None:
        print(f"❌ '{filename}' naam ki koi file Saved Messages mein nahi mili.")
        return
    print(f"✅ Mil gayi! File: {name} | Size: {size} bytes")
    
    # 7️⃣ High-speed download (8 workers)
    output_path = f"/content/{name}"
    print("⏳ Download chal raha hai (Full Bandwidth, 8 workers)...")
    try:
        await download_telegram_file(client, file_id, output_path, workers=8)
        print(f"✅ Download complete: {output_path}")
    except Exception as e:
        print(f"❌ Download error: {e}")
        return
    
    # 8️⃣ Terabox par upload (sirf token use hoga)
    print("⏳ Terabox par upload ho raha hai...")
    ndus_token = creds['ndus_token']
    try:
        link = upload_to_terabox(output_path, ndus_token)
        print(f"✅ Upload Complete! 🔗 Download Link: {link}")
    except Exception as e:
        print(f"❌ Upload error: {e}")
    finally:
        # 9️⃣ Local file delete (Jagah bachao)
        if os.path.exists(output_path):
            os.remove(output_path)
            print("🧹 Local file delete kar di.")
    
    await client.stop()
    print("✅ Sab khatam! Bot band ho gaya.")

if __name__ == "__main__":
    asyncio.run(main())