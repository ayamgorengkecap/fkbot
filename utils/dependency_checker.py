"""Check optional dependencies and provide graceful fallback"""

def check_instagram_support():
    """Check if Instagram dependencies are installed"""
    try:
        import instagrapi
        import pydantic
        return True
    except ImportError:
        return False

def check_telegram_support():
    """Check if Telegram dependencies are installed"""
    try:
        from telethon import TelegramClient
        return True
    except ImportError:
        return False

def check_dependencies():
    """Check all dependencies"""
    status = {
        'requests': False,
        'instagram': False,
        'telegram': False
    }
    
    try:
        import requests
        status['requests'] = True
    except ImportError:
        pass
    
    status['instagram'] = check_instagram_support()
    status['telegram'] = check_telegram_support()
    
    return status

def get_missing_dependencies():
    """Get list of missing optional dependencies"""
    missing = []
    
    if not check_instagram_support():
        missing.append('Instagram: pip install instagrapi pydantic Pillow')
    
    if not check_telegram_support():
        missing.append('Telegram: pip install Telethon cryptography pyaes rsa')
    
    return missing
