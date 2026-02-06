#!/usr/bin/env python3
import os
import sys
import json
import time
import base64
import random
import requests
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

CONFIG_FILE = "config.json"
ENCRYPT_KEY = b"pepekirwmfdi1234"  # 16 bytes for AES
DASH_URL = "https://cryptofuture.co.in/dashboard"
EARN_URL = "https://cryptofuture.co.in/earn"

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def encrypt(data, key):
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(data.encode(), AES.block_size))
    return base64.b64encode(iv + encrypted).decode()

def decrypt(data, key):
    raw = base64.b64decode(data)
    iv = raw[:16]
    encrypted = raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(encrypted), AES.block_size).decode()

def http_request(url, method='GET', data=None, headers=None):
    while True:
        try:
            if method.upper() == 'POST':
                resp = requests.post(url, data=data, headers=headers, timeout=60)
            else:
                resp = requests.get(url, headers=headers, timeout=60)
            return resp.text
        except:
            print("\033[33mRetrying...\033[0m", end='\r')
            time.sleep(1)
            continue

def timer(seconds, message="[!] please wait"):
    remaining = int(seconds)
    spinners = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    idx = 0
    while remaining > 0:
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        secs = remaining % 60
        spinner = spinners[idx % len(spinners)]
        print(f"\033[37m{message}\033[32m {hours:02d}:{mins:02d}:{secs:02d} \033[37m{spinner}\r", end='')
        time.sleep(1)
        remaining -= 1
        idx += 1
    print("\r" + " " * 50 + "\r", end='')

def widget_id():
    uuid = ''
    for i in range(32):
        if i in [8, 12, 16, 20]:
            uuid += '-'
        r = random.randint(0, 15)
        if i == 12:
            r = 4
        elif i == 16:
            r = (r & 0x3) | 0x8
        uuid += format(r, 'x')
    return uuid

def solve_captcha(token, headers, url):
    wid = widget_id()
    ts = int(time.time() * 1000)
    init_ts = ts - 5000
    
    payload = {
        "widgetId": wid,
        "action": "LOAD",
        "theme": "light",
        "token": token,
        "timestamp": ts,
        "initTimestamp": init_ts
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    resp = http_request(url, "POST", f"payload={encoded}", headers)
    decoded = json.loads(base64.b64decode(resp))
    identifier = decoded["identifier"]
    
    for x in [20, 60, 100, 140, 180, 220, 260, 300]:
        ts = int(time.time() * 1000)
        init_ts = ts - 5000
        sel_payload = {
            "widgetId": wid,
            "challengeId": identifier,
            "action": "SELECTION",
            "x": x,
            "y": random.randint(20, 30),
            "width": 320,
            "token": token,
            "timestamp": ts,
            "initTimestamp": init_ts
        }
        encoded = base64.b64encode(json.dumps(sel_payload).encode()).decode()
        resp = http_request(url, "POST", f"payload={encoded}", headers)
        decoded = json.loads(base64.b64decode(resp))
        if decoded.get("completed") == "1":
            return {"widget": wid, "identifier": identifier}
        print("\033[33msolving captcha...\033[0m", end='\r')
        time.sleep(1)
    return None

def get_headers(cookie, user_agent, extra=None):
    h = {
        "Host": "cryptofuture.co.in",
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "id,en-US;q=0.9,en;q=0.8",
        "Referer": "https://cryptofuture.co.in/earn",
        "Cookie": cookie
    }
    if extra:
        h.update(extra)
    return h

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None, None
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        cookie = decrypt(config['cookie'], ENCRYPT_KEY)
        ua = decrypt(config['user-agent'], ENCRYPT_KEY)
        return cookie, ua
    except:
        return None, None

def save_config(cookie, user_agent):
    config = {
        "cookie": encrypt(cookie, ENCRYPT_KEY),
        "user-agent": encrypt(user_agent, ENCRYPT_KEY)
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def extract_value(html, pattern):
    import re
    match = re.search(pattern, html)
    return match.group(1) if match else None

def main():
    clear()
    cookie, user_agent = load_config()
    
    if not cookie or not user_agent:
        print("\033[37m[Setup]\033[0m")
        cookie = input("cookie: ").strip()
        if not cookie:
            print("\033[31mCookie required!\033[0m")
            return
        user_agent = input("user-agent: ").strip()
        if not user_agent:
            print("\033[31mUser-agent required!\033[0m")
            return
        save_config(cookie, user_agent)
        print("\033[32mConfig saved!\033[0m")
        time.sleep(1)
    
    clear()
    headers = get_headers(cookie, user_agent)
    
    # Check login
    dash = http_request(DASH_URL, headers=headers)
    try:
        user_id = dash.split('<div class="fw-bold fs-6">')[1].split('</div>')[0]
    except:
        user_id = None
    
    if not user_id:
        print("\033[31mCookie expired! Delete config.json and retry.\033[0m")
        os.remove(CONFIG_FILE)
        return
    
    print(f"\033[37mUserID: \033[36m{user_id}\033[0m")
    
    # Get currencies
    earn = http_request(EARN_URL, headers=headers)
    import re
    currencies = re.findall(r'href="https://cryptofuture\.co\.in/faucet/currency/([a-zA-Z]+)"', earn)
    currencies = list(dict.fromkeys(currencies))  # Remove duplicates
    currencies.sort(key=len)
    
    print("\033[37mAvailable:\033[0m")
    for i, c in enumerate(currencies, 1):
        print(f"\033[32m{i}\033[37m.{c.upper():5}", end="  ")
        if i % 5 == 0:
            print()
    print(f"\n\033[37m(all) = run all\033[0m")
    
    choice = input("\033[37mchoose: \033[0m").strip().lower()
    
    if choice == 'all':
        selected = currencies
    else:
        try:
            idx = int(choice) - 1
            selected = [currencies[idx]]
        except:
            print("\033[31mInvalid choice\033[0m")
            return
    
    print(f"\033[32mSelected: {', '.join(selected)}\033[0m\n")
    
    while True:
        all_limit = True
        for coin in selected:
            url = f"https://cryptofuture.co.in/faucet/currency/{coin}"
            page = http_request(url, headers=headers)
            
            if "Please verify your account via Telegram" in page:
                code = page.split('cryptofuturefaucet_bot?start=')[1].split('"')[0]
                print(f"\033[33mVerify Telegram: https://t.me/cryptofuturefaucet_bot?start={code}\033[0m")
                input("Press enter after verification...")
                continue
            
            if "Daily claim limit for this coin reached" in page:
                print(f"\033[33m{coin.upper()} limit reached\033[0m")
                continue
            
            all_limit = False
            
            csrf = extract_value(page, r'name="csrf_token_name"[^>]*value="([^"]*)"')
            token = extract_value(page, r'name="token"[^>]*value="([^"]*)"')
            wallet = extract_value(page, r'name="wallet"[^>]*value="([^"]*)"')
            captcha_token = extract_value(page, r"name='_iconcaptcha-token'[^>]*value='([^']*)'")
            action = extract_value(page, r'<form id="fauform"[^>]*action="([^"]*)"')
            wait = extract_value(page, r'var wait = (\d+)')
            
            if not all([csrf, token, wallet, captcha_token, action]):
                print("\033[33mReloading...\033[0m")
                time.sleep(2)
                continue
            
            if wait:
                timer(int(wait))
            
            captcha_headers = {
                "Host": "cryptofuture.co.in",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": user_agent,
                "X-Iconcaptcha-Token": captcha_token,
                "Origin": "https://cryptofuture.co.in",
                "Referer": url,
                "Cookie": cookie
            }
            
            result = solve_captcha(captcha_token, captcha_headers, "https://cryptofuture.co.in/icaptcha/req")
            if not result:
                continue
            
            post_data = {
                "csrf_token_name": csrf,
                "token": token,
                "jscheck": "8|501x1114|Asia/Jakarta",
                "adblock_check": "",
                "captcha": "icaptcha",
                "_iconcaptcha-token": captcha_token,
                "ic-rq": "1",
                "ic-wid": result["widget"],
                "ic-cid": result["identifier"],
                "ic-hp": "",
                "wallet": wallet
            }
            
            post_headers = get_headers(cookie, user_agent, {
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://cryptofuture.co.in"
            })
            
            resp = http_request(action, "POST", post_data, post_headers)
            
            try:
                msg = resp.split("html: '")[2].split("'")[0]
                msg = re.sub(r'<[^>]+>', '', msg)
                print(f"\033[32m{msg}\033[0m")
            except:
                print(f"\033[32m{coin.upper()} claimed!\033[0m")
            
            wait = extract_value(resp, r'var wait = (\d+)')
            if wait:
                timer(int(wait))
        
        if all_limit:
            print("\033[33mAll coins reached daily limit\033[0m")
            now = datetime.now()
            if now.hour >= 7:
                reset = datetime(now.year, now.month, now.day + 1, 7, 1)
            else:
                reset = datetime(now.year, now.month, now.day, 7, 1)
            wait_secs = (reset - now).total_seconds()
            print(f"\033[37mReset at 07:01 WIB\033[0m")
            timer(int(wait_secs))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[31mStopped\033[0m")
