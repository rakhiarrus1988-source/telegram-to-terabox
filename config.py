import json
import os
from google.colab import drive

CONFIG_PATH = "/content/drive/MyDrive/telegram_user_config.json"
SESSION_DIR = "/content/drive/MyDrive/telegram_sessions"
SESSION_NAME = "user_session"   # Pyrogram session file will be saved here

def mount_drive():
    drive.mount('/content/drive')
    os.makedirs(SESSION_DIR, exist_ok=True)

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def get_credentials():
    config = load_config()
    required = ['api_id', 'api_hash', 'phone', 'ndus_cookies']
    missing = [k for k in required if k not in config]
    if missing:
        print(f"⚠️ Missing credentials: {missing}")
        for key in missing:
            if key == 'ndus_cookies':
                print("Enter NDUS cookies as a string: e.g., 'key1=value1; key2=value2'")
            config[key] = input(f"Enter {key}: ").strip()
        save_config(config)
        print("✅ Credentials saved to Drive.")
    return config

def get_session_path():
    return os.path.join(SESSION_DIR, SESSION_NAME)