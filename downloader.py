import asyncio
import aiohttp
import os
import time
from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.errors import RPCError

async def get_file_location(client: Client, file_id: str):
    """
    Use raw API to get file location (dc_id, file_path, size, name).
    """
    # Get the file info using raw GetFile
    try:
        # file_id is a string, we need to convert to InputFileLocation
        # We can use client.get_messages to get the message and then extract the location
        # But simpler: use the raw API with file_id
        # However, raw GetFile expects InputFileLocation object.
        # Instead, we can use client.get_file which returns a File object
        # Let's try to use client.get_file properly.
        file = await client.get_file(file_id)
        # file is an object with attributes: dc_id, file_path, file_size, file_name
        return file.dc_id, file.file_path, file.file_size, file.file_name
    except Exception as e:
        raise Exception(f"get_file_location failed: {e}")

async def download_chunk(session, url, start, end, chunk_dir, part_num, progress_callback=None):
    headers = {'Range': f'bytes={start}-{end}'}
    async with session.get(url, headers=headers) as resp:
        if resp.status == 206:
            data = await resp.read()
            part_path = os.path.join(chunk_dir, f'part_{part_num}')
            with open(part_path, 'wb') as f:
                f.write(data)
            if progress_callback:
                progress_callback(len(data))
        else:
            raise Exception(f"Chunk {part_num} failed with status {resp.status}")

async def download_telegram_file(client: Client, file_id: str, output_path: str, workers: int = 8):
    """
    Multi‑worker chunk download with progress. If fails, fallback to client.download_media with progress.
    """
    # Try multi-worker
    try:
        dc_id, file_path, file_size, file_name = await get_file_location(client, file_id)
        if file_size == 0:
            raise ValueError("File size is zero.")
        
        # Construct CDN URL
        url = f"https://dc{dc_id}.telegram.org/file/{file_path}"
        chunk_size = file_size // workers
        os.makedirs('temp_chunks', exist_ok=True)
        
        # Progress tracking
        downloaded = 0
        def progress_callback(chunk_bytes):
            nonlocal downloaded
            downloaded += chunk_bytes
            percent = (downloaded / file_size) * 100
            bar = '█' * int(percent // 2) + '-' * (50 - int(percent // 2))
            print(f"\r⏳ Downloading: [{bar}] {percent:.1f}% ({downloaded}/{file_size} bytes)", end='', flush=True)
        
        tasks = []
        async with aiohttp.ClientSession() as session:
            for i in range(workers):
                start = i * chunk_size
                end = (i + 1) * chunk_size - 1 if i < workers - 1 else file_size - 1
                tasks.append(download_chunk(session, url, start, end, 'temp_chunks', i, progress_callback))
            await asyncio.gather(*tasks)
        
        print()  # newline after progress
        
        # Combine parts
        with open(output_path, 'wb') as out:
            for i in range(workers):
                part_path = os.path.join('temp_chunks', f'part_{i}')
                with open(part_path, 'rb') as f:
                    out.write(f.read())
                os.remove(part_path)
        os.rmdir('temp_chunks')
        print("✅ Multi‑worker download successful!")
        return
    except Exception as e:
        print(f"\n⚠️ Multi‑worker download failed: {e}")
        print("🔄 Falling back to Pyrogram's built‑in download_media (single‑threaded)...")
        # Fallback: use client.download_media with progress
        def progress_callback(current, total):
            percent = (current / total) * 100
            bar = '█' * int(percent // 2) + '-' * (50 - int(percent // 2))
            print(f"\r⏳ Fallback download: [{bar}] {percent:.1f}% ({current}/{total} bytes)", end='', flush=True)
        
        try:
            downloaded_path = await client.download_media(file_id, file_name=output_path, progress=progress_callback)
            print()  # newline
            if downloaded_path:
                print(f"✅ Fallback download successful: {downloaded_path}")
                return
            else:
                raise Exception("Fallback download returned None.")
        except Exception as e2:
            raise Exception(f"Fallback download also failed: {e2}")