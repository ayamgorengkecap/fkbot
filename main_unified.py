#!/usr/bin/env python3
"""
VKSerbot Unified v2 - Single Entry Point
=========================================
Menggabungkan Auto Register dan Auto Task dalam satu project.

PENTING: File ini adalah WRAPPER/ENTRY POINT saja.
         Semua logika asli TIDAK diubah.

Struktur:
  - lib/register_bot.py      : Logika register ASLI
  - lib/automation_core.py   : Logika task ASLI  
  - modules/register.py      : Wrapper untuk register
  - modules/tasks.py         : Wrapper untuk tasks
  - modules/accounts.py      : Manajemen akun dengan duplicate check

Cara pakai TANPA venv:
  pip install -r requirements.txt
  python3 main.py
"""
import sys
import os
import re
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'lib'))
sys.path.insert(0, os.path.join(BASE_DIR, 'utils'))
sys.path.insert(0, os.path.join(BASE_DIR, 'modules'))

from modules.accounts import list_accounts, load_account, find_duplicate_accounts
from modules.register import register_accounts, register_single_account
from modules.tasks import run_all_accounts

G = '\033[92m'
R = '\033[91m'
Y = '\033[93m'
C = '\033[96m'
W = '\033[0m'
B = '\033[94m'

def show_banner():
    """Display banner"""
    os.system('clear' if os.name != 'nt' else 'cls')
    print(f"{C}┌{'─' * 58}┐{W}")
    print(f"{C}│{W}  {G}██╗   ██╗{C}██╗  ██╗{R}███████╗{W}  UNIFIED BOT              {C}│{W}")
    print(f"{C}│{W}  {G}██║   ██║{C}██║ ██╔╝{R}██╔════╝{W}  Register + Tasks          {C}│{W}")
    print(f"{C}│{W}  {G}██║   ██║{C}█████╔╝ {R}███████╗{W}                            {C}│{W}")
    print(f"{C}│{W}  {G}╚██╗ ██╔╝{C}██╔═██╗ {R}╚════██║{W}  Created by: @aldo_tamvan {C}│{W}")
    print(f"{C}│{W}   {G}╚████╔╝ {C}██║  ██╗{R}███████║{W}                            {C}│{W}")
    print(f"{C}│{W}    {G}╚═══╝  {C}╚═╝  ╚═╝{R}╚══════╝{W}  v2.0 Unified             {C}│{W}")
    print(f"{C}└{'─' * 58}┘{W}")

def show_menu():
    """Display main menu"""
    accounts = list_accounts()
    
    print(f"\n{C}{'='*60}{W}")
    print(f"{C}MAIN MENU{W} (Accounts: {G}{len(accounts)}{W})")
    print(f"{C}{'='*60}{W}")
    print(f"{G}1.{W} Register new accounts (from data/*.txt)")
    print(f"{G}2.{W} Register single account (manual input)")
    print(f"{G}3.{W} Run tasks on all accounts (parallel)")
    print(f"{G}4.{W} Run tasks on all accounts (sequential)")
    print(f"{G}5.{W} List all accounts")
    print(f"{G}6.{W} Find duplicate accounts")
    print(f"{G}7.{W} Run original main.py (full features)")
    print(f"{C}{'='*60}{W}")
    print(f"{R}0.{W} Exit")
    print(f"{C}{'='*60}{W}")

def list_accounts_menu():
    """Show all accounts"""
    accounts = list_accounts()
    
    print(f"\n{C}{'='*60}{W}")
    print(f"{C}ACCOUNTS LIST ({len(accounts)} total){W}")
    print(f"{C}{'='*60}{W}")
    
    if not accounts:
        print(f"{Y}No accounts found. Register first!{W}")
        return
    
    for acc in accounts:
        config = load_account(acc)
        if not config:
            print(f"  {R}✗{W} {acc}: Config error")
            continue
        
        vk_id = config.get('vk_api', {}).get('user_id', 'N/A')
        ig_enabled = config.get('instagram', {}).get('enabled', False)
        tg_enabled = config.get('telegram', {}).get('enabled', False)
        
        ig_status = f"{G}✓{W}" if ig_enabled else f"{R}✗{W}"
        tg_status = f"{G}✓{W}" if tg_enabled else f"{R}✗{W}"
        
        print(f"  {G}✓{W} {acc} (VK: {vk_id}) [IG: {ig_status}] [TG: {tg_status}]")
    
    print(f"{C}{'='*60}{W}")

def manual_register():
    """Register single account manually"""
    print(f"\n{C}{'='*60}{W}")
    print(f"{C}MANUAL REGISTRATION{W}")
    print(f"{C}{'='*60}{W}")
    
    email = input(f"{C}Email: {W}").strip()
    if not email:
        print(f"{R}Email required!{W}")
        return
    
    vk_token_full = input(f"{C}VK Token (full URL or token): {W}").strip()
    if not vk_token_full:
        print(f"{R}VK token required!{W}")
        return
    
    match = re.search(r'access_token=([^&]+).*user_id=(\d+)', vk_token_full)
    if not match:
        print(f"{R}Invalid VK token format!{W}")
        print(f"{Y}Expected: ...access_token=XXX...&user_id=123...{W}")
        return
    
    vk_token = match.group(1)
    vk_id = match.group(2)
    
    proxy = input(f"{C}Proxy (IP:PORT:USER:PASS): {W}").strip()
    if not proxy:
        print(f"{R}Proxy required!{W}")
        return
    
    password = input(f"{C}Password (default: Aldo123##): {W}").strip() or "Aldo123##"
    
    print(f"\n{Y}Starting registration...{W}")
    result = register_single_account(email, vk_token, vk_id, proxy, password)
    
    if result:
        print(f"\n{G}✅ SUCCESS! Account saved: {result}{W}")
    else:
        print(f"\n{R}❌ Registration failed!{W}")

def run_original_main():
    """Run the original main.py with full features"""
    import subprocess
    original_main = os.path.join(BASE_DIR, 'main_original.py')
    if os.path.exists(original_main):
        subprocess.run([sys.executable, original_main])
    else:
        print(f"{Y}Original main not found, copying...{W}")
        import shutil
        src = os.path.join(BASE_DIR, 'main.py.bak')
        if os.path.exists(src):
            shutil.copy(src, original_main)
            subprocess.run([sys.executable, original_main])
        else:
            print(f"{R}Cannot find original main.py{W}")

def main():
    """Main entry point"""
    while True:
        show_banner()
        show_menu()
        
        choice = input(f"\n{C}Select option: {W}").strip()
        
        if choice == '1':
            register_accounts()
        
        elif choice == '2':
            manual_register()
        
        elif choice == '3':
            run_all_accounts(parallel=True)
        
        elif choice == '4':
            run_all_accounts(parallel=False)
        
        elif choice == '5':
            list_accounts_menu()
        
        elif choice == '6':
            duplicates = find_duplicate_accounts()
            print(f"\n{C}{'='*60}{W}")
            print(f"{C}DUPLICATE CHECK{W}")
            print(f"{C}{'='*60}{W}")
            if duplicates:
                print(f"{Y}Found {len(duplicates)} duplicate(s):{W}")
                for acc1, acc2, reason in duplicates:
                    print(f"  - {acc1} <-> {acc2}: {reason}")
            else:
                print(f"{G}No duplicates found!{W}")
            print(f"{C}{'='*60}{W}")
        
        elif choice == '7':
            run_original_main()
        
        elif choice == '0':
            print(f"\n{G}Goodbye!{W}")
            break
        
        else:
            print(f"{R}Invalid option!{W}")
        
        input(f"\n{Y}Press Enter to continue...{W}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Y}Interrupted by user{W}")
        sys.exit(0)
