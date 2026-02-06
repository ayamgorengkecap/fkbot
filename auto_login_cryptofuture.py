#!/usr/bin/env python3
"""
Auto Login CryptoFuture - curl_cffi Edition
Bypass Cloudflare + Auto Captcha + Email Only Login
"""
import os
import sys
import json
import time
import base64
import re
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_OK = True
except ImportError:
    CURL_CFFI_OK = False

import requests as std_requests

CONFIG_FILE = "config.json"
ENCRYPT_KEY = b"pepekirwmfdi1234"
BASE_URL = "https://cryptofuture.co.in"
DASH_URL = "https://cryptofuture.co.in/dashboard"
AUTH_URL = "https://cryptofuture.co.in/auth/login"
CAPTCHA_URL = "https://cryptofuture.co.in/icaptcha/req"

G, R, Y, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[96m', '\033[0m'

USER_AGENT = "Mozilla/5.0 (Linux; Android 15; TECNO LI9 Build/AP3A.240905.015.A2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7559.59 Mobile Safari/537.36"

def encrypt(data, key):
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(data.encode(), AES.block_size))
    return base64.b64encode(iv + encrypted).decode()

def save_config(cookie, user_agent):
    config = {
        "cookie": encrypt(cookie, ENCRYPT_KEY),
        "user-agent": encrypt(user_agent, ENCRYPT_KEY)
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"{G}Config saved to {CONFIG_FILE}!{W}")

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

def solve_captcha(token, session, cookies):
    """Solve IconCaptcha via API"""
    wid = widget_id()
    ts = int(time.time() * 1000)
    
    headers = {
        'Host': 'cryptofuture.co.in',
        'X-Requested-With': 'XMLHttpRequest',
        'X-Iconcaptcha-Token': token,
        'Origin': 'https://cryptofuture.co.in',
        'Referer': 'https://cryptofuture.co.in/',
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    # Load captcha
    payload = {
        'widgetId': wid,
        'action': 'LOAD',
        'theme': 'light',
        'token': token,
        'timestamp': ts,
        'initTimestamp': ts - 5000
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    
    resp = session.post(CAPTCHA_URL, data=f'payload={encoded}', headers=headers, cookies=cookies)
    
    try:
        # Handle whitespace in response
        resp_text = resp.text.strip()
        decoded = json.loads(base64.b64decode(resp_text))
        identifier = decoded.get('identifier')
        print(f"    Captcha loaded: {identifier[:20]}...")
    except Exception as e:
        print(f"{R}    Captcha load failed: {e}{W}")
        return None
    
    # Try different X positions
    positions = [20, 60, 100, 140, 180, 220, 260, 300]
    
    for x in positions:
        ts = int(time.time() * 1000)
        sel_payload = {
            'widgetId': wid,
            'challengeId': identifier,
            'action': 'SELECTION',
            'x': x,
            'y': random.randint(20, 30),
            'width': 320,
            'token': token,
            'timestamp': ts,
            'initTimestamp': ts - 5000
        }
        encoded = base64.b64encode(json.dumps(sel_payload).encode()).decode()
        
        resp = session.post(CAPTCHA_URL, data=f'payload={encoded}', headers=headers, cookies=cookies)
        
        try:
            resp_text = resp.text.strip()
            decoded = json.loads(base64.b64decode(resp_text))
            if decoded.get('completed'):
                print(f"{G}    Captcha solved at x={x}!{W}")
                return {'widget': wid, 'identifier': identifier}
        except:
            pass
        
        time.sleep(0.3)
    
    print(f"{R}    Captcha failed (all positions tried){W}")
    return None

def auto_login_curl_cffi(email):
    """Auto login using curl_cffi (best CF bypass)"""
    print(f"\n{C}{'='*55}{W}")
    print(f"{C}CryptoFuture Auto Login (curl_cffi){W}")
    print(f"{C}Email: {email}{W}")
    print(f"{C}{'='*55}{W}\n")
    
    if not CURL_CFFI_OK:
        print(f"{R}curl_cffi not installed!{W}")
        print(f"Install: pip install curl_cffi --break-system-packages")
        return None
    
    # Create session with Chrome impersonation
    session = curl_requests.Session(impersonate='chrome')
    
    print(f"{Y}[1] Opening homepage...{W}")
    resp = session.get(BASE_URL)
    
    if resp.status_code != 200:
        print(f"{R}    Failed! Status: {resp.status_code}{W}")
        return None
    
    if "Just a moment" in resp.text:
        print(f"{R}    Cloudflare challenge detected!{W}")
        return None
    
    print(f"{G}    Page loaded!{W}")
    
    # Extract tokens
    csrf_match = re.search(r'name="csrf_token_name"[^>]*value="([^"]*)"', resp.text)
    captcha_match = re.search(r"name='_iconcaptcha-token'[^>]*value='([^']*)'", resp.text)
    
    if not csrf_match or not captcha_match:
        print(f"{R}    Form tokens not found!{W}")
        return None
    
    csrf_token = csrf_match.group(1)
    captcha_token = captcha_match.group(1)
    cookies = dict(resp.cookies)
    
    print(f"    CSRF: {csrf_token[:25]}...")
    print(f"    Captcha: {captcha_token[:25]}...")
    
    print(f"\n{Y}[2] Solving captcha...{W}")
    captcha_result = solve_captcha(captcha_token, session, cookies)
    
    if not captcha_result:
        print(f"{R}    Captcha solving failed!{W}")
        return None
    
    print(f"\n{Y}[3] Submitting login...{W}")
    
    login_data = {
        'wallet': email,
        'csrf_token_name': csrf_token,
        'captcha': 'icaptcha',
        '_iconcaptcha-token': captcha_token,
        'ic-rq': '1',
        'ic-wid': captcha_result['widget'],
        'ic-cid': captcha_result['identifier'],
        'ic-hp': ''
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://cryptofuture.co.in',
        'Referer': 'https://cryptofuture.co.in/',
        'User-Agent': USER_AGENT,
    }
    
    resp = session.post(AUTH_URL, data=login_data, headers=headers, cookies=cookies)
    print(f"    Login response: {resp.status_code}")
    
    # Update cookies
    cookies.update(dict(resp.cookies))
    
    print(f"\n{Y}[4] Checking dashboard...{W}")
    resp = session.get(DASH_URL, cookies=cookies)
    print(f"    Dashboard status: {resp.status_code}")
    
    cookies.update(dict(resp.cookies))
    
    # Check for user ID
    user_match = re.search(r'<div class="fw-bold fs-6">(\d+)</div>', resp.text)
    
    if user_match:
        user_id = user_match.group(1)
        print(f"\n{G}{'='*55}{W}")
        print(f"{G}LOGIN SUCCESSFUL!{W}")
        print(f"{G}UserID: {user_id}{W}")
        print(f"{G}{'='*55}{W}\n")
        
        # Build cookie string
        cookie_str = '; '.join([f'{k}={v}' for k, v in cookies.items()])
        
        print(f"{C}Cookies:{W}")
        for k, v in cookies.items():
            print(f"  {k}: {v[:40]}...")
        
        # Save config
        save_config(cookie_str, USER_AGENT)
        
        print(f"\n{G}{'='*55}{W}")
        print(f"{G}Jalankan: python3 bot_clean.py{W}")
        print(f"{G}{'='*55}{W}")
        
        return cookie_str
    else:
        print(f"\n{R}LOGIN FAILED!{W}")
        
        if "verify" in resp.text.lower() or "telegram" in resp.text.lower():
            # Extract Telegram verification link
            tg_match = re.search(r'href="(https://t\.me/cryptofuturefaucet_bot\?start=[^"]+)"', resp.text)
            if tg_match:
                print(f"{Y}Perlu verifikasi Telegram!{W}")
                print(f"{C}Link: {tg_match.group(1)}{W}")
                print(f"\n{Y}Setelah verifikasi, jalankan script ini lagi.{W}")
            else:
                print(f"{Y}Perlu verifikasi (check email/telegram){W}")
        elif "Invalid" in resp.text:
            print(f"{R}Email tidak terdaftar di FaucetPay!{W}")
        else:
            print(f"{Y}Unknown error - check screenshot{W}")
        
        return None

def test_cookie(cookie_str):
    """Test if existing cookie works"""
    headers = {
        "Host": "cryptofuture.co.in",
        "User-Agent": USER_AGENT,
        "Cookie": cookie_str,
    }
    
    try:
        resp = std_requests.get(DASH_URL, headers=headers, timeout=30)
        if resp.status_code == 200:
            match = re.search(r'<div class="fw-bold fs-6">(\d+)</div>', resp.text)
            if match:
                return True, f"UserID: {match.group(1)}"
        return False, "Session expired or invalid"
    except Exception as e:
        return False, str(e)

def manual_cookie_input():
    """Manual cookie paste mode"""
    print(f"\n{C}{'='*55}{W}")
    print(f"{C}Manual Cookie Input{W}")
    print(f"{C}{'='*55}{W}\n")
    
    print(f"{Y}Paste cookie dari browser (ci_session=xxx; ...){W}\n")
    
    cookie = input("Cookie: ").strip()
    if not cookie:
        print(f"{R}Cookie required!{W}")
        return None
    
    cookie = cookie.replace("cookie:", "").replace("Cookie:", "").strip()
    
    print(f"\n{Y}Testing...{W}")
    valid, msg = test_cookie(cookie)
    
    if valid:
        print(f"{G}{msg}{W}")
        save_config(cookie, USER_AGENT)
        return cookie
    else:
        print(f"{R}Failed: {msg}{W}")
        save = input(f"\n{Y}Save anyway? (y/n): {W}").strip().lower()
        if save == 'y':
            save_config(cookie, USER_AGENT)
        return None

def main():
    print(f"{C}╔═══════════════════════════════════════════════════════╗{W}")
    print(f"{C}║         CryptoFuture Auto Login                       ║{W}")
    print(f"{C}║    Bypass CF + Email Only + Auto Captcha              ║{W}")
    print(f"{C}╚═══════════════════════════════════════════════════════╝{W}\n")
    
    # Check curl_cffi
    if CURL_CFFI_OK:
        print(f"  curl_cffi: {G}OK{W}")
    else:
        print(f"  curl_cffi: {R}NOT INSTALLED{W}")
        print(f"  Install: pip install curl_cffi --break-system-packages\n")
    
    print(f"\nMode:")
    print(f"  {G}1{W}. Auto Login (curl_cffi) {Y}<- RECOMMENDED{W}")
    print(f"  {G}2{W}. Manual Cookie (paste)")
    print(f"  {G}0{W}. Cancel")
    
    choice = input(f"\nPilihan: ").strip()
    
    if choice == '1':
        if not CURL_CFFI_OK:
            print(f"\n{R}curl_cffi tidak terinstall!{W}")
            return
        
        email = input(f"\nEmail (FaucetPay): ").strip()
        if not email:
            print(f"{R}Email required!{W}")
            return
        
        auto_login_curl_cffi(email)
        
    elif choice == '2':
        manual_cookie_input()
    
    else:
        print(f"{Y}Cancelled{W}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{R}Cancelled{W}")
