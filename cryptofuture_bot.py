#!/usr/bin/env python3
"""
CryptoFuture All-in-One Bot
- Auto Login (curl_cffi bypass CF)
- Auto Captcha Solver
- Auto Claim Faucet
"""
import os
import sys
import json
import time
import base64
import re
import random
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

try:
    from curl_cffi import requests
    CURL_CFFI_OK = True
except ImportError:
    CURL_CFFI_OK = False
    import requests

CONFIG_FILE = "config.json"
ENCRYPT_KEY = b"pepekirwmfdi1234"
BASE_URL = "https://cryptofuture.co.in"
DASH_URL = "https://cryptofuture.co.in/dashboard"
EARN_URL = "https://cryptofuture.co.in/earn"
AUTH_URL = "https://cryptofuture.co.in/auth/login"
CAPTCHA_URL = "https://cryptofuture.co.in/icaptcha/req"

G, R, Y, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[96m', '\033[0m'

USER_AGENT = "Mozilla/5.0 (Linux; Android 15; TECNO LI9 Build/AP3A.240905.015.A2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7559.59 Mobile Safari/537.36"

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def encrypt(data, key):
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(data.encode(), AES.block_size))
    return base64.b64encode(iv + encrypted).decode()

def decrypt(data, key):
    raw = base64.b64decode(data)
    iv, encrypted = raw[:16], raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(encrypted), AES.block_size).decode()

def save_config(cookie, user_agent):
    config = {"cookie": encrypt(cookie, ENCRYPT_KEY), "user-agent": encrypt(user_agent, ENCRYPT_KEY)}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None, None
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return decrypt(config['cookie'], ENCRYPT_KEY), decrypt(config['user-agent'], ENCRYPT_KEY)
    except:
        return None, None

def widget_id():
    uuid = ''
    for i in range(32):
        if i in [8, 12, 16, 20]: uuid += '-'
        r = random.randint(0, 15)
        if i == 12: r = 4
        elif i == 16: r = (r & 0x3) | 0x8
        uuid += format(r, 'x')
    return uuid

def timer(seconds, message="[!] please wait"):
    remaining = int(seconds)
    spinners = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    idx = 0
    while remaining > 0:
        h, m, s = remaining // 3600, (remaining % 3600) // 60, remaining % 60
        print(f"{W}{message}{G} {h:02d}:{m:02d}:{s:02d} {W}{spinners[idx % 8]}\r", end='')
        time.sleep(1)
        remaining -= 1
        idx += 1
    print("\r" + " " * 50 + "\r", end='')

class CryptoFutureBot:
    def __init__(self, email=None):
        self.email = email
        self.cookie = None
        self.user_agent = USER_AGENT
        self.session = None
        self.user_id = None
        
    def create_session(self):
        """Create session with CF bypass"""
        if CURL_CFFI_OK:
            self.session = requests.Session(impersonate='chrome')
        else:
            self.session = requests.Session()
            self.session.headers.update({'User-Agent': self.user_agent})
    
    def solve_captcha(self, token, cookies):
        """Solve IconCaptcha"""
        wid = widget_id()
        ts = int(time.time() * 1000)
        
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'X-Iconcaptcha-Token': token,
            'Origin': BASE_URL,
            'Referer': f'{BASE_URL}/',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        # Load
        payload = {'widgetId': wid, 'action': 'LOAD', 'theme': 'light', 'token': token, 'timestamp': ts, 'initTimestamp': ts - 5000}
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        resp = self.session.post(CAPTCHA_URL, data=f'payload={encoded}', headers=headers, cookies=cookies)
        
        try:
            decoded = json.loads(base64.b64decode(resp.text.strip()))
            identifier = decoded.get('identifier')
        except:
            return None
        
        # Solve
        for x in [20, 60, 100, 140, 180, 220, 260, 300]:
            ts = int(time.time() * 1000)
            sel = {'widgetId': wid, 'challengeId': identifier, 'action': 'SELECTION', 'x': x, 'y': random.randint(20, 30), 'width': 320, 'token': token, 'timestamp': ts, 'initTimestamp': ts - 5000}
            encoded = base64.b64encode(json.dumps(sel).encode()).decode()
            resp = self.session.post(CAPTCHA_URL, data=f'payload={encoded}', headers=headers, cookies=cookies)
            try:
                if json.loads(base64.b64decode(resp.text.strip())).get('completed'):
                    return {'widget': wid, 'identifier': identifier}
            except:
                pass
            time.sleep(0.3)
        return None
    
    def login(self):
        """Auto login with email"""
        if not self.email:
            print(f"{R}Email not set!{W}")
            return False
        
        print(f"{Y}[LOGIN] Email: {self.email}{W}")
        self.create_session()
        
        # Get homepage - wait for CF cookies
        print(f"{Y}  Opening homepage...{W}")
        resp = self.session.get(BASE_URL)
        
        # Wait for CF to set cookies
        print(f"{Y}  Waiting for CF cookies...{W}")
        time.sleep(3)
        
        if resp.status_code != 200:
            print(f"{R}  Failed! Status: {resp.status_code}{W}")
            return False
        
        if "Just a moment" in resp.text:
            print(f"{Y}  CF challenge, waiting...{W}")
            time.sleep(5)
            resp = self.session.get(BASE_URL)
        
        cookies = dict(resp.cookies)
        print(f"{G}  Cookies: {list(cookies.keys())}{W}")
        
        # Get tokens
        csrf = re.search(r'name="csrf_token_name"[^>]*value="([^"]*)"', resp.text)
        captcha = re.search(r"name='_iconcaptcha-token'[^>]*value='([^']*)'", resp.text)
        if not csrf or not captcha:
            print(f"{R}  Tokens not found!{W}")
            return False
        
        # Solve captcha
        print(f"{Y}  Solving captcha...{W}")
        result = self.solve_captcha(captcha.group(1), cookies)
        if not result:
            print(f"{R}  Captcha failed!{W}")
            return False
        print(f"{G}  Captcha solved!{W}")
        
        # Submit login
        print(f"{Y}  Submitting login...{W}")
        data = {
            'wallet': self.email,
            'csrf_token_name': csrf.group(1),
            'captcha': 'icaptcha',
            '_iconcaptcha-token': captcha.group(1),
            'ic-rq': '1',
            'ic-wid': result['widget'],
            'ic-cid': result['identifier'],
            'ic-hp': ''
        }
        resp = self.session.post(AUTH_URL, data=data, cookies=cookies)
        cookies.update(dict(resp.cookies))
        
        # Wait for session to establish
        print(f"{Y}  Waiting for session...{W}")
        time.sleep(3)
        
        # Check dashboard
        resp = self.session.get(DASH_URL, cookies=cookies)
        cookies.update(dict(resp.cookies))
        
        # Wait again for any CF cookies
        time.sleep(2)
        
        # Get all cookies from session
        try:
            if hasattr(self.session, 'cookies'):
                session_cookies = self.session.cookies
                if hasattr(session_cookies, 'items'):
                    for k, v in session_cookies.items():
                        cookies[k] = v
                elif hasattr(session_cookies, '__iter__'):
                    for c in session_cookies:
                        if hasattr(c, 'name') and hasattr(c, 'value'):
                            cookies[c.name] = c.value
        except:
            pass
        
        user = re.search(r'<div class="fw-bold fs-6">(\d+)</div>', resp.text)
        if user:
            self.user_id = user.group(1)
            
            # Build cookie string with all cookies
            self.cookie = '; '.join([f'{k}={v}' for k, v in cookies.items()])
            
            # Save config
            save_config(self.cookie, self.user_agent)
            
            print(f"{G}  Login success! UserID: {self.user_id}{W}")
            print(f"{G}  Cookies saved: {list(cookies.keys())}{W}")
            return True
        
        # Check for Telegram verification
        tg = re.search(r'(https://t\.me/cryptofuturefaucet_bot\?start=[^\s"<>]+)', resp.text)
        if tg:
            print(f"{Y}  Perlu verifikasi Telegram!{W}")
            print(f"{C}  Link: {tg.group(1)}{W}")
        else:
            print(f"{R}  Login failed! (mungkin email belum terdaftar){W}")
        return False
    
    def check_session(self):
        """Check if saved session is valid"""
        cookie, ua = load_config()
        if not cookie:
            return False
        
        self.cookie = cookie
        self.user_agent = ua or USER_AGENT
        self.create_session()
        
        headers = {'Cookie': self.cookie, 'User-Agent': self.user_agent}
        
        try:
            if CURL_CFFI_OK:
                resp = self.session.get(DASH_URL, headers=headers)
            else:
                resp = self.session.get(DASH_URL, headers=headers)
            
            user = re.search(r'<div class="fw-bold fs-6">(\d+)</div>', resp.text)
            if user:
                self.user_id = user.group(1)
                return True
        except:
            pass
        return False
    
    def get_currencies(self):
        """Get available currencies"""
        headers = {'Cookie': self.cookie, 'User-Agent': self.user_agent}
        resp = self.session.get(EARN_URL, headers=headers)
        currencies = re.findall(r'href="https://cryptofuture\.co\.in/faucet/currency/([a-zA-Z]+)"', resp.text)
        return list(dict.fromkeys(currencies))
    
    def claim_faucet(self, coin):
        """Claim faucet for specific coin"""
        url = f"{BASE_URL}/faucet/currency/{coin}"
        headers = {'Cookie': self.cookie, 'User-Agent': self.user_agent}
        
        resp = self.session.get(url, headers=headers)
        html = resp.text
        
        # Check Telegram verification
        if "Please verify your account via Telegram" in html:
            tg = re.search(r'(https://t\.me/cryptofuturefaucet_bot\?start=[^\s"<>]+)', html)
            if tg:
                print(f"{Y}Verify Telegram: {tg.group(1)}{W}")
            return "verify"
        
        # Check limit
        if "Daily claim limit for this coin reached" in html:
            return "limit"
        
        # Get form data
        csrf = re.search(r'name="csrf_token_name"[^>]*value="([^"]*)"', html)
        token = re.search(r'name="token"[^>]*value="([^"]*)"', html)
        wallet = re.search(r'name="wallet"[^>]*value="([^"]*)"', html)
        captcha_token = re.search(r"name='_iconcaptcha-token'[^>]*value='([^']*)'", html)
        action = re.search(r'<form id="fauform"[^>]*action="([^"]*)"', html)
        wait = re.search(r'var wait = (\d+)', html)
        
        if not all([csrf, token, wallet, captcha_token, action]):
            return "error"
        
        # Wait
        if wait:
            timer(int(wait.group(1)), f"[{coin.upper()}] Waiting")
        
        # Solve captcha
        cookies = {c.split('=')[0]: c.split('=')[1] for c in self.cookie.split('; ')}
        result = self.solve_captcha(captcha_token.group(1), cookies)
        if not result:
            return "captcha_fail"
        
        # Submit claim
        post_data = {
            'csrf_token_name': csrf.group(1),
            'token': token.group(1),
            'jscheck': '8|501x1114|Asia/Jakarta',
            'adblock_check': '',
            'captcha': 'icaptcha',
            '_iconcaptcha-token': captcha_token.group(1),
            'ic-rq': '1',
            'ic-wid': result['widget'],
            'ic-cid': result['identifier'],
            'ic-hp': '',
            'wallet': wallet.group(1)
        }
        
        post_headers = {
            'Cookie': self.cookie,
            'User-Agent': self.user_agent,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': BASE_URL,
        }
        
        resp = self.session.post(action.group(1), data=post_data, headers=post_headers)
        
        # Parse result
        try:
            msg = resp.text.split("html: '")[2].split("'")[0]
            msg = re.sub(r'<[^>]+>', '', msg)
            print(f"{G}{msg}{W}")
        except:
            print(f"{G}{coin.upper()} claimed!{W}")
        
        # Next wait
        wait = re.search(r'var wait = (\d+)', resp.text)
        if wait:
            timer(int(wait.group(1)), f"[{coin.upper()}] Next claim")
        
        return "success"
    
    def run_faucet(self, coins=None):
        """Run faucet claiming loop"""
        if not self.cookie:
            print(f"{R}Not logged in!{W}")
            return
        
        print(f"\n{C}{'='*50}{W}")
        print(f"{C}Starting Faucet Claim - UserID: {self.user_id}{W}")
        print(f"{C}{'='*50}{W}\n")
        
        # Get currencies
        available = self.get_currencies()
        if not available:
            print(f"{R}No currencies found!{W}")
            return
        
        if coins:
            selected = [c for c in coins if c.upper() in [a.upper() for a in available]]
        else:
            selected = available
        
        print(f"{Y}Coins: {', '.join([c.upper() for c in selected])}{W}\n")
        
        while True:
            all_limit = True
            
            for coin in selected:
                print(f"{Y}[{coin.upper()}] Claiming...{W}")
                result = self.claim_faucet(coin)
                
                if result == "verify":
                    print(f"{R}Need Telegram verification!{W}")
                    return
                elif result == "limit":
                    print(f"{Y}[{coin.upper()}] Daily limit reached{W}")
                elif result == "success":
                    all_limit = False
                elif result == "captcha_fail":
                    print(f"{R}[{coin.upper()}] Captcha failed, retrying...{W}")
                    all_limit = False
                
                time.sleep(1)
            
            if all_limit:
                print(f"\n{Y}All coins reached daily limit!{W}")
                now = datetime.now()
                if now.hour >= 7:
                    reset = datetime(now.year, now.month, now.day, 7, 1)
                    if now.hour >= 7:
                        from datetime import timedelta
                        reset += timedelta(days=1)
                else:
                    reset = datetime(now.year, now.month, now.day, 7, 1)
                
                wait_secs = (reset - now).total_seconds()
                print(f"{Y}Reset at 07:01 WIB{W}")
                timer(int(wait_secs), "Waiting for reset")

def main():
    clear()
    print(f"{C}╔═══════════════════════════════════════════════════════╗{W}")
    print(f"{C}║         CryptoFuture All-in-One Bot                   ║{W}")
    print(f"{C}║    Auto Login + Auto Captcha + Auto Claim             ║{W}")
    print(f"{C}╚═══════════════════════════════════════════════════════╝{W}\n")
    
    if CURL_CFFI_OK:
        print(f"  curl_cffi: {G}OK{W} (CF Bypass enabled)")
    else:
        print(f"  curl_cffi: {R}NOT INSTALLED{W}")
        print(f"  Install: pip install curl_cffi --break-system-packages\n")
    
    bot = CryptoFutureBot()
    
    # Check existing session
    print(f"\n{Y}Checking saved session...{W}")
    if bot.check_session():
        print(f"{G}Session valid! UserID: {bot.user_id}{W}")
    else:
        print(f"{Y}No valid session, need to login{W}")
        
        email = input(f"\n{W}Email (FaucetPay): {W}").strip()
        if not email:
            print(f"{R}Email required!{W}")
            return
        
        bot.email = email
        if not bot.login():
            print(f"\n{R}Login failed! Fix the issue and try again.{W}")
            return
    
    # Show menu
    print(f"\n{Y}Mode:{W}")
    print(f"  {G}1{W}. Claim ALL coins")
    print(f"  {G}2{W}. Select specific coin")
    print(f"  {G}0{W}. Exit")
    
    choice = input(f"\nPilihan: ").strip()
    
    if choice == '1':
        bot.run_faucet()
    elif choice == '2':
        currencies = bot.get_currencies()
        print(f"\n{Y}Available:{W}")
        for i, c in enumerate(currencies, 1):
            print(f"  {G}{i}{W}. {c.upper()}")
        
        sel = input(f"\nPilih nomor (pisah koma untuk multiple): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in sel.split(',')]
            selected = [currencies[i] for i in indices if 0 <= i < len(currencies)]
            if selected:
                bot.run_faucet(selected)
        except:
            print(f"{R}Invalid selection{W}")
    else:
        print(f"{Y}Bye!{W}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{R}Stopped{W}")
