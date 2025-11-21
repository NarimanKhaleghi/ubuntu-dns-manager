import json
import os

CONFIG_FILE = os.path.expanduser("~/.ubuntu_dns_manager_config.json")

DEFAULT_CONFIG = {
    "language": "EN",  # Default must be EN
    "update_urls": [
        "https://raw.githubusercontent.com/blacklanternsecurity/public-dns-servers/refs/heads/master/nameservers.txt"
    ],
    "test_domain": "google.com",
    "auto_clean_enabled": False, # Disabled by default
    "ping_limit": 400,
    "speed_limit": 300
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            for key, val in DEFAULT_CONFIG.items():
                if key not in data:
                    data[key] = val
            return data
    except:
        return DEFAULT_CONFIG

def save_config(key, value):
    config = load_config()
    config[key] = value
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def get_setting(key):
    return load_config().get(key, DEFAULT_CONFIG.get(key))