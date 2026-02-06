"""Registration module - WRAPPER ONLY
Calls original register_bot.py logic without modifications
"""
import os
import sys
import re
import time
import random
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'lib'))

from lib.register_bot import VKSerfingBot as VKSerfingRegisterBot
from lib.vk_api_wrapper import VKApi
from modules.accounts import create_new_account

G = '\033[92m'
R = '\033[91m'
Y = '\033[93m'
C = '\033[96m'
W = '\033[0m'

# 2Captcha config
CAPTCHA_API_KEY = 'a7572b136ea51733734c662a9d8e94c5'
MIN_CAPTCHA_BALANCE = 0.1  # USD

# Donation addresses
DONATION_ADDRESSES = {
    'TRX (Tron)': 'TGhiKfFiSXVcczSv7jU8yfCdGT6SsDPn4A',
    'LTC (Litecoin)': 'ltc1q8nqp78edgyu23hdxhh85tanra3x3anq9658uvx',
    'BSC (BNB/USDT)': '0x8ee88f8c183c74cef93b31c508c2af809ff0c6d2',
}


def get_2captcha_balance():
    """Get 2captcha balance in USD"""
    try:
        resp = requests.get(f'http://2captcha.com/res.php?key={CAPTCHA_API_KEY}&action=getbalance&json=1', timeout=10)
        data = resp.json()
        if data.get('status') == 1:
            return float(data.get('request', 0))
    except:
        pass
    return 0.0


def show_donation_prompt():
    """Show donation addresses and wait for balance"""
    print(f"\n{R}{'='*60}{W}")
    print(f"{R}⚠️  SALDO 2CAPTCHA TIDAK CUKUP (< ${MIN_CAPTCHA_BALANCE}){W}")
    print(f"{R}{'='*60}{W}")
    print(f"\n{Y}Untuk melanjutkan register, diperlukan saldo 2Captcha.{W}")
    print(f"{Y}Silakan donate minimal ${MIN_CAPTCHA_BALANCE} USD ke salah satu alamat berikut:{W}\n")
    
    for name, addr in DONATION_ADDRESSES.items():
        print(f"  {C}{name}:{W}")
        print(f"  {G}{addr}{W}\n")
    
    print(f"{Y}{'='*60}{W}")
    print(f"{Y}📝 NOTE: Setelah donate, tunggu 1-5 menit untuk proses.{W}")
    print(f"{Y}{'='*60}{W}")
    print(f"\n{C}Mengecek saldo 2Captcha setiap 15 detik...{W}")
    print(f"{Y}Tekan Ctrl+C untuk membatalkan.{W}\n")


def wait_for_captcha_balance():
    """Wait for 2captcha balance to be sufficient, checking every 15 seconds"""
    show_donation_prompt()
    
    try:
        while True:
            # Countdown timer 15 seconds
            for remaining in range(15, 0, -1):
                balance = get_2captcha_balance()
                status = f"Saldo: ${balance:.3f} USD"
                print(f"\r  ⏳ Checking in {remaining:2d}s... | {status}", end="", flush=True)
                time.sleep(1)
            
            # Check balance
            balance = get_2captcha_balance()
            print(f"\r  🔄 Checking balance... Saldo: ${balance:.3f} USD", end="", flush=True)
            
            if balance >= MIN_CAPTCHA_BALANCE:
                print(f"\n\n{G}✅ Saldo cukup! (${balance:.3f} USD){W}\n")
                
                while True:
                    choice = input(f"{Y}Lanjut register? (y/n): {W}").strip().lower()
                    if choice in ['y', 'yes']:
                        return True
                    elif choice in ['n', 'no']:
                        print(f"{Y}Register dibatalkan.{W}")
                        return False
                    print(f"{R}Pilih y atau n{W}")
            else:
                print(f"\n  {Y}Saldo masih kurang (${balance:.3f} < ${MIN_CAPTCHA_BALANCE}). Menunggu...{W}\n")
    
    except KeyboardInterrupt:
        print(f"\n\n{Y}Dibatalkan oleh user.{W}")
        return False


def check_captcha_balance_or_donate():
    """Check 2captcha balance, if insufficient show donation prompt"""
    print(f"\n{C}🔍 Checking 2Captcha balance...{W}")
    balance = get_2captcha_balance()
    print(f"   Saldo: ${balance:.3f} USD")
    
    if balance >= MIN_CAPTCHA_BALANCE:
        print(f"   {G}✅ Saldo cukup untuk register{W}")
        return True
    else:
        return wait_for_captcha_balance()

def read_file_lines(filename):
    """Read lines from file"""
    filepath = BASE_DIR / filename
    try:
        with open(filepath) as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def load_input_data():
    """Load emails, vk_tokens, proxies from data/"""
    emails = read_file_lines('data/emails.txt')
    vk_tokens = read_file_lines('data/vk_tokens.txt')
    proxies = read_file_lines('data/proxies.txt')
    
    accounts = []
    for i in range(min(len(emails), len(vk_tokens), len(proxies))):
        match = re.search(r'access_token=([^&]+).*user_id=(\d+)', vk_tokens[i])
        if match:
            accounts.append({
                'email': emails[i],
                'vk_token': match.group(1),
                'vk_id': match.group(2),
                'proxy': proxies[i],
                'password': 'Aldo123##'
            })
    
    return accounts

def register_single_account(email, vk_token, vk_id, proxy, password='Aldo123##'):
    """Register single account using ORIGINAL register_bot.py logic"""
    try:
        # Pre-check: Verify no duplicate VK ID or email BEFORE registration
        from modules.accounts import check_duplicate_vk_id, check_duplicate_email
        
        existing_vk = check_duplicate_vk_id(vk_id)
        if existing_vk:
            print(f"{R}❌ VK ID {vk_id} sudah terdaftar di: {existing_vk}{W}")
            print(f"{Y}   Skipping untuk mencegah duplicate...{W}")
            return None
        
        existing_email = check_duplicate_email(email)
        if existing_email:
            print(f"{R}❌ Email {email} sudah terdaftar di: {existing_email}{W}")
            print(f"{Y}   Skipping untuk mencegah duplicate...{W}")
            return None
        
        bot = VKSerfingRegisterBot(proxy)
        vk = VKApi(vk_token, vk_id)
        
        print(f"\n{C}🔍 Checking VK profile...{W}")
        profile = vk.users_get()
        if not profile:
            print(f"{R}❌ Failed to get VK profile{W}")
            return None
        
        user = profile[0]
        print(f"{G}✅ VK: {user.get('first_name')} {user.get('last_name')}{W}")
        
        print(f"{C}⚙️  Setting up profile...{W}")
        countries_data = [
            {'id': 1, 'title': 'Russia', 'cities': ['Moscow', 'Saint Petersburg', 'Novosibirsk']},
            {'id': 2, 'title': 'Ukraine', 'cities': ['Kyiv', 'Kharkiv', 'Odesa']},
            {'id': 3, 'title': 'Belarus', 'cities': ['Minsk', 'Gomel', 'Mogilev']},
        ]
        
        country_data = random.choice(countries_data)
        home_town = random.choice(country_data['cities'])
        year = random.randint(1989, 2006)
        bdate = f"{random.randint(1,28)}.{random.randint(1,12)}.{year}"
        
        vk.set_profile(bdate=bdate, home_town=home_town)
        print(f"{G}   ✓ {country_data['title']}, {home_town}, {bdate}{W}")
        time.sleep(2)
        
        print(f"{C}📝 Registering on VKSerfing...{W}")
        if not bot.register(email, password):
            print(f"{R}❌ Registration failed{W}")
            return None
        
        print(f"{C}🔑 Getting phrase...{W}")
        phrase_text, phrase_hash = bot.get_phrase()
        if not phrase_text:
            print(f"{R}❌ Failed to get phrase{W}")
            return None
        
        print(f"{G}📝 Phrase: {phrase_text}{W}")
        
        print(f"{C}📝 Setting VK bio...{W}")
        vk.set_bio(phrase_text)
        time.sleep(5)
        
        print(f"{C}🔗 Binding VK...{W}")
        if not bot.bind_vk(vk_id, phrase_hash):
            print(f"{R}❌ Binding failed{W}")
            return None
        
        print(f"{G}✅ VK bound{W}")
        
        print(f"{C}🧹 Clearing VK bio...{W}")
        vk.set_bio('')
        time.sleep(2)
        
        proxy_parts = proxy.split(':')
        proxy_config = {
            'proxy_string': f'http://{proxy_parts[2]}:{proxy_parts[3]}@{proxy_parts[0]}:{proxy_parts[1]}' if len(proxy_parts) == 4 else proxy,
            'ip': proxy_parts[0] if len(proxy_parts) >= 2 else 'unknown',
            'country': 'Various',
            'city': 'Proxy',
            'verified_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        config = {
            'proxy': proxy_config,
            'user_agent': {
                'user_agent': bot.user_agent,
                'device': bot.device_info['device'],
                'model': bot.device_info['model'],
                'android_version': bot.device_info['android'],
                'chrome_version': bot.device_info['chrome']
            },
            'credentials': {
                'cookies': bot.cookies,
                'xsrf_token': bot.xsrf_token
            },
            'settings': {
                'wait_time_min': 11,
                'wait_time_max': 21,
                'delay_between_tasks': 25,
                'auto_mode': True
            },
            'task_types': {
                'vk_friends': True,
                'vk_groups': True,
                'vk_likes': True,
                'vk_reposts': True,
                'vk_polls': True,
                'vk_videos': True,
                'vk_views': True,
                'telegram_followers': False,
                'telegram_views': False,
                'instagram_followers': False,
                'instagram_likes': False
            },
            'vk_api': {
                'enabled': True,
                'user_id': vk_id,
                'access_token': vk_token
            },
            'instagram': {'enabled': False},
            'telegram': {'enabled': False}
        }
        
        # Pass email for duplicate checking during save
        account_name = create_new_account(config, email=email)
        if account_name:
            print(f"{G}✅ Account saved: {account_name}{W}")
        else:
            print(f"{Y}⚠️  Account tidak disimpan (mungkin duplicate){W}")
        
        return account_name
        
    except Exception as e:
        print(f"{R}❌ ERROR: {e}{W}")
        import traceback
        traceback.print_exc()
        return None

def register_accounts(mode='batch'):
    """Register accounts from input files - WRAPPER"""
    print(f"\n{C}{'='*60}{W}")
    print(f"{C}📝 AUTO REGISTER MODE{W}")
    print(f"{C}{'='*60}{W}")
    
    # Check 2captcha balance first
    if not check_captcha_balance_or_donate():
        return []
    
    accounts_data = load_input_data()
    
    if not accounts_data:
        print(f"{R}❌ No accounts found in data/ files!{W}")
        print(f"{Y}   Make sure data/emails.txt, data/vk_tokens.txt, data/proxies.txt exist{W}")
        return []
    
    print(f"{G}✅ Loaded {len(accounts_data)} accounts from files{W}")
    
    registered = []
    
    print(f"\n{C}🚀 Starting registration...{W}")
    for idx, acc in enumerate(accounts_data, 1):
        print(f"\n{C}{'='*60}{W}")
        print(f"{C}【 ACCOUNT {idx}/{len(accounts_data)} 】{W}")
        print(f"{C}Email: {acc['email']}{W}")
        print(f"{C}VK ID: {acc['vk_id']}{W}")
        print(f"{C}{'='*60}{W}")
        
        result = register_single_account(
            acc['email'], acc['vk_token'], acc['vk_id'], 
            acc['proxy'], acc['password']
        )
        
        if result:
            registered.append(result)
        
        if idx < len(accounts_data):
            delay = random.randint(20, 50)
            print(f"\n{Y}⏳ Waiting {delay}s before next account...{W}")
            time.sleep(delay)
    
    print(f"\n{C}{'='*60}{W}")
    print(f"{G}✅ Registration complete! Registered: {len(registered)} accounts{W}")
    print(f"{C}{'='*60}{W}")
    
    return registered
