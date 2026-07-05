import asyncio
import aiohttp
import os
from pyrogram import Client
from pyrogram.errors import RPCError

async def get_file_url_and_size(client: Client, file_id: str):
    """Get direct download URL and file size using Pyrogram's get_file."""
    try:
        file = await client.get_file(file_id)
        dc_id = file.dc_id
        file_path = file.file_path
        url = f"https://dc{dc_id}.telegram.org/file/{file_path}"
        return url, file.file_size
    except Exception as e:
        raise Exception(f"get_file failed: {e}")

async def download_chunk(session, url, start, end, chunk_dir, part_num):
    headers = {'Range': f'bytes={start}-{end}'}
    async with session.get(url, headers=headers) as resp:
        if resp.status == 206:
            data = await resp.read()
            part_path = os.path.join(chunk_dir, f'part_{part_num}')
            with open(part_path, 'wb') as f:
                f.write(data)
        else:
            raise Exception(f"Chunk {part_num} failed with status {resp.status}")

async def download_telegram_file(client: Client, file_id: str, output_path: str, workers: int = 8):
    """
    Multi‑worker chunk download. Agar fail ho toh fallback as client.download_media use karega.
    """
    try:
        # Try to get URL and size
        url, file_size = await get_file_url_and_size(client, file_id)
        if file_size == 0:
            raise ValueError("File size is zero.")
        
        chunk_size = file_size // workers
        os.makedirs('temp_chunks', exist_ok=True)
        tasks = []
        async with aiohttp.ClientSession() as session:
            for i in range(workers):
                start = i * chunk_size
                end = (i + 1) * chunk_size - 1 if i < workers - 1 else file_size - 1
                tasks.append(download_chunk(session, url, start, end, 'temp_chunks', i))
            await asyncio.gather(*tasks)
        
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
        print(f"⚠️ Multi‑worker download failed: {e}")
        print("🔄 Falling back to Pyrogram's built‑in download_media (single‑threaded)...")
        # Fallback: use client.download_media
        # download_media is async; it returns the file path
        downloaded_path = await client.download_media(file_id, file_name=output_path)
        if downloaded_path:
            print(f"✅ Fallback download successful: {downloaded_path}")
            return
        else:
            raise Exception("Fallback download also failed.")