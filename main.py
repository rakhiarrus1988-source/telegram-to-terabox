import asyncio
import os
from pyrogram import Client
from config import get_credentials, mount_drive, get_session_path
from downloader import download_telegram_file
from uploader import upload_to_terabox

async def search_file_in_saved_messages(client, filename):
    print("🔍 Saved Messages mein search ho raha hai...")
    # ✅ Pyrogram v2 ka sahī tarīqā – get_chat_history
    async for msg in client.get_chat_history('me', limit=2000):
        if msg.document and msg.document.file_name and filename.lower() in msg.document.file_name.lower():
            return msg.document.file_id, msg.document.file_name, msg.document.file_size
        elif msg.video and msg.video.file_name and filename.lower() in msg.video.file_name.lower():
            return msg.video.file_id, msg.video.file_name, msg.video.file_size
        elif msg.audio and msg.audio.file_name and filename.lower() in msg.audio.file_name.lower():
            return msg.audio.file_id, msg.audio.file_name, msg.audio.file_size
    return None, None, None

async def main():
    mount_drive()
    creds = get_credentials()
    
    client = Client(
        get_session_path(),
        api_id=int(creds['api_id']),
        api_hash=creds['api_hash'],
        phone_number=creds['phone']
    )
    
    try:
        await client.start()
        print("✅ Telegram Login Successful!")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return
    
    filename = input("\n📁 File name (or part) jo Saved Messages mein hai: ").strip()
    if not filename:
        print("❌ Kuch likha nahi!")
        return
    
    file_id, name, size = await search_file_in_saved_messages(client, filename)
    if file_id is None:
        print(f"❌ '{filename}' nahi mili.")
        return
    print(f"✅ Mil gayi! {name} | Size: {size} bytes")
    
    output_path = f"/content/{name}"
    print("⏳ Downloading with 8 workers (Full Bandwidth)...")
    await download_telegram_file(client, file_id, output_path, workers=8)
    print("✅ Download complete!")
    
    print("⏳ Uploading to Terabox...")
    link = upload_to_terabox(output_path, creds['ndus_token'])
    print(f"✅ Upload Done! 🔗 {link}")
    
    os.remove(output_path)
    await client.stop()
    print("✅ Sab khatam!")

if __name__ == "__main__":
    asyncio.run(main())