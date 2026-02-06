#!/usr/bin/env python3
"""
Auto Login Telegram Web using Playwright
- Opens Telegram Web
- Waits for QR code scan from mobile app
- Saves session for reuse
"""

import asyncio
import os
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    exit(1)


SESSION_DIR = Path(__file__).parent / "data" / "telegram_web_sessions"
TELEGRAM_WEB_URL = "https://web.telegram.org/k/"


async def login_telegram_web(session_name: str = "default", headless: bool = False):
    """
    Login to Telegram Web via QR code scan.
    
    Args:
        session_name: Name for the session folder
        headless: Run browser in headless mode (False to see QR code)
    """
    session_path = SESSION_DIR / session_name
    session_path.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=headless,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        print(f"[*] Opening Telegram Web...")
        await page.goto(TELEGRAM_WEB_URL, wait_until="domcontentloaded")
        
        # Check if already logged in
        try:
            await page.wait_for_selector(".chat-list", timeout=5000)
            print("[+] Already logged in! Session restored.")
            await browser.close()
            return True
        except:
            pass
        
        # Wait for QR code
        print("[*] Waiting for QR code to appear...")
        try:
            await page.wait_for_selector("canvas.qr-canvas, .qr-container canvas", timeout=30000)
            print("\n" + "="*50)
            print("QR CODE READY - Scan with Telegram mobile app!")
            print("Go to: Settings > Devices > Link Desktop Device")
            print("="*50 + "\n")
        except:
            print("[!] QR code not found. Page might have changed.")
        
        # Wait for successful login (chat list appears)
        print("[*] Waiting for login... (scan QR code now)")
        try:
            await page.wait_for_selector(".chat-list, .chatlist", timeout=120000)
            print("[+] Login successful!")
            
            # Give it time to sync
            await asyncio.sleep(3)
            print(f"[+] Session saved to: {session_path}")
            
        except:
            print("[!] Login timeout. Please try again.")
            await browser.close()
            return False
        
        await browser.close()
        return True


async def check_session(session_name: str = "default"):
    """Check if a saved session is still valid."""
    session_path = SESSION_DIR / session_name
    
    if not session_path.exists():
        print(f"[-] No session found: {session_name}")
        return False
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=True,
            viewport={"width": 1280, "height": 800}
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await page.goto(TELEGRAM_WEB_URL, wait_until="domcontentloaded")
        
        try:
            await page.wait_for_selector(".chat-list, .chatlist", timeout=15000)
            print(f"[+] Session '{session_name}' is valid!")
            await browser.close()
            return True
        except:
            print(f"[-] Session '{session_name}' is invalid or expired.")
            await browser.close()
            return False


async def list_sessions():
    """List all saved sessions."""
    if not SESSION_DIR.exists():
        print("No sessions found.")
        return []
    
    sessions = [d.name for d in SESSION_DIR.iterdir() if d.is_dir()]
    if sessions:
        print("Saved sessions:")
        for s in sessions:
            print(f"  - {s}")
    else:
        print("No sessions found.")
    return sessions


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Telegram Web Auto Login")
    parser.add_argument("action", choices=["login", "check", "list"], 
                        help="Action to perform")
    parser.add_argument("-s", "--session", default="default",
                        help="Session name (default: 'default')")
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode (not recommended for login)")
    
    args = parser.parse_args()
    
    if args.action == "login":
        asyncio.run(login_telegram_web(args.session, args.headless))
    elif args.action == "check":
        asyncio.run(check_session(args.session))
    elif args.action == "list":
        asyncio.run(list_sessions())


if __name__ == "__main__":
    main()
