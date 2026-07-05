import asyncio
import os
import time
from pyrogram import Client
from pyrogram.errors import RPCError
from config import get_credentials, mount_drive, get_session_path
from downloader import download_telegram_file
from uploader import upload_to_terabox

async def search_file_in_saved_messages(client, filename):
    print("🔍 Saved Messages mein search ho raha hai...")
    print("📋 Saare file names neeche print ho rahe hain (check karo):")
    print("-" * 60)
    
    file_list = []  # Store all files with their details
    async for msg in client.get_chat_history('me', limit=5000):
        if msg.document and msg.document.file_name:
            fname = msg.document.file_name
            file_list.append((msg.document.file_id, fname, msg.document.file_size, 'document'))
            print(f"📄 {fname}")
        elif msg.video and msg.video.file_name:
            fname = msg.video.file_name
            file_list.append((msg.video.file_id, fname, msg.video.file_size, 'video'))
            print(f"🎬 {fname}")
        elif msg.audio and msg.audio.file_name:
            fname = msg.audio.file_name
            file_list.append((msg.audio.file_id, fname, msg.audio.file_size, 'audio'))
            print(f"🎵 {fname}")
    
    print("-" * 60)
    print(f"✅ Total {len(file_list)} files scan kiye.")
    
    # Search with multiple strategies
    search_term = filename.lower().strip()
    
    # 1. Exact match (case-insensitive)
    for fid, fname, fsize, ftype in file_list:
        if fname.lower().strip() == search_term:
            return fid, fname, fsize
    
    # 2. Partial match (filename contains search term)
    for fid, fname, fsize, ftype in file_list:
        if search_term in fname.lower():
            return fid, fname, fsize
    
    # 3. Partial match with extension removed (if user gave with extension)
    if '.' in search_term:
        base = search_term.split('.')[0]
        for fid, fname, fsize, ftype in file_list:
            if base in fname.lower():
                return fid, fname, fsize
    
    return None, None, None

async def main():
    mount_drive()
    creds = get_credentials()
    
    session_path = get_session_path()
    # Agar pehle session corrupt ho toh delete karo
    if os.path.exists(session_path + ".lock"):
        print("⚠️ Purana session lock mila, delete kar raha hoon...")
        os.remove(session_path + ".lock")
    
    client = Client(
        session_path,
        api_id=int(creds['api_id']),
        api_hash=creds['api_hash'],
        phone_number=creds['phone']
    )
    
    try:
        await client.start()
        print("✅ Telegram Login Successful!")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        # Agar database locked, toh session file delete karke retry
        if "database is locked" in str(e):
            print("🔄 Database locked, session file delete kar raha hoon...")
            if os.path.exists(session_path + ".session"):
                os.remove(session_path + ".session")
            print("✅ Session file delete ho gayi. Ab script dobara chalao.")
        return
    
    filename = input("\n📁 File name (or part) jo Saved Messages mein hai: ").strip()
    if not filename:
        print("❌ Kuch likha nahi!")
        await client.stop()
        return
    
    file_id, name, size = await search_file_in_saved_messages(client, filename)
    if file_id is None:
        print(f"❌ '{filename}' nahi mili.")
        print("💡 Upar list mein dekho – agar file naam wahan nahi hai toh:")
        print("   - File Saved Messages mein nahi hai")
        print("   - Ya aapne galat spelling/part daali hai")
        print("   - Ya file kisi aur chat mein hai (forward kari ho)")
        await client.stop()
        return
    
    print(f"✅ Mil gayi! {name} | Size: {size} bytes")
    
    output_path = f"/content/{name}"
    print("⏳ Downloading with 8 workers (Full Bandwidth)...")
    try:
        await download_telegram_file(client, file_id, output_path, workers=8)
        print("✅ Download complete!")
    except Exception as e:
        print(f"❌ Download error: {e}")
        await client.stop()
        return
    
    print("⏳ Uploading to Terabox...")
    try:
        link = upload_to_terabox(output_path, creds['ndus_token'])
        print(f"✅ Upload Done! 🔗 {link}")
    except Exception as e:
        print(f"❌ Upload error: {e}")
    
    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)
        print("🧹 Local file delete kar di.")
    
    await client.stop()
    print("✅ Sab khatam! Client safely stopped.")

if __name__ == "__main__":
    asyncio.run(main())