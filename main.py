import asyncio
import os
from pyrogram import Client
from pyrogram.errors import RPCError
from config import get_credentials, mount_drive, get_session_path
from downloader import download_telegram_file
from uploader import upload_to_terabox

async def search_file_in_saved_messages(client, filename):
    """Search Saved Messages for a file with matching name."""
    saved_messages = await client.get_messages('me', limit=1000)  # adjust limit as needed
    for msg in saved_messages:
        # Check document, video, audio, etc.
        if msg.document and msg.document.file_name and filename.lower() in msg.document.file_name.lower():
            return msg.document.file_id, msg.document.file_name, msg.document.file_size
        elif msg.video and msg.video.file_name and filename.lower() in msg.video.file_name.lower():
            return msg.video.file_id, msg.video.file_name, msg.video.file_size
        elif msg.audio and msg.audio.file_name and filename.lower() in msg.audio.file_name.lower():
            return msg.audio.file_id, msg.audio.file_name, msg.audio.file_size
    return None, None, None

async def main():
    # Mount Drive and load credentials
    mount_drive()
    creds = get_credentials()
    
    # Create client with session file in Drive
    session_path = get_session_path()
    client = Client(
        session_path,
        api_id=int(creds['api_id']),
        api_hash=creds['api_hash'],
        phone_number=creds['phone']
    )
    
    # Start client (will prompt for OTP if needed)
    try:
        await client.start()
        print("✅ Logged in to Telegram successfully!")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    # Ask for file name to search
    filename = input("\nEnter the file name (or part of it) to download from Saved Messages: ").strip()
    if not filename:
        print("No file name provided. Exiting.")
        return
    
    # Search in Saved Messages
    file_id, name, size = await search_file_in_saved_messages(client, filename)
    if file_id is None:
        print(f"❌ No file found with name containing '{filename}' in Saved Messages.")
        return
    print(f"✅ Found file: {name} (Size: {size} bytes)")
    
    # Download using multi-worker
    output_path = f"/content/{name}"
    print("⏳ Downloading with full bandwidth (8 workers)...")
    try:
        await download_telegram_file(client, file_id, output_path, workers=8)
        print(f"✅ Downloaded to {output_path}")
    except Exception as e:
        print(f"❌ Download error: {e}")
        return
    
    # Upload to Terabox
    print("⏳ Uploading to Terabox using NDUS cookies...")
    ndus_cookies = creds['ndus_cookies']
    try:
        download_link = upload_to_terabox(output_path, ndus_cookies)
        print(f"✅ Upload successful! 🔗 {download_link}")
    except Exception as e:
        print(f"❌ Upload error: {e}")
    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)
            print("🧹 Cleaned up local file.")
    
    await client.stop()

if __name__ == "__main__":
    asyncio.run(main())