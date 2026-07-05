import json
import os
from google.colab import drive

CONFIG_PATH = "/content/drive/MyDrive/telegram_user_config.json"
SESSION_DIR = "/content/drive/MyDrive/telegram_sessions"
SESSION_NAME = "user_session"

def mount_drive():
    print("🔄 Mounting Google Drive... (Colab will ask for permissions)")
    drive.mount('/content/drive')
    os.makedirs(SESSION_DIR, exist_ok=True)
    print("✅ Drive mounted successfully!")

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
    # Ab 'ndus_cookies' ki jagah 'ndus_token'
    required = ['api_id', 'api_hash', 'phone', 'ndus_token']
    missing = [k for k in required if k not in config]
    if missing:
        print(f"⚠️ Pehli baar chal raha hai! Neeche diye gaye credentials daalein:")
        for key in missing:
            if key == 'phone':
                print("  (Phone number with country code, e.g., +911234567890)")
            if key == 'ndus_token':
                print("  (Sirf token string daalein, jaise: abc123xyz)")
            config[key] = input(f"Enter {key}: ").strip()
        save_config(config)
        print("✅ Sab credentials Drive par save ho gaye! Ab baar baar nahi poochunga.")
    return config

def get_session_path():
    return os.path.join(SESSION_DIR, SESSION_NAME)