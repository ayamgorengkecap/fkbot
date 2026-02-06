#!/usr/bin/env python3
"""
FKBot - VKSerbot Unified
========================
Auto Register + Auto Task dalam satu menu.
"""
import sys
import os
import re
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'lib'))
sys.path.insert(0, os.path.join(BASE_DIR, 'utils'))
sys.path.insert(0, os.path.join(BASE_DIR, 'modules'))

from modules.accounts import list_accounts, load_account, find_duplicate_accounts, create_new_account
from modules.register import register_accounts, register_single_account
from modules.tasks import run_all_accounts

G = '\033[92m'
R = '\033[91m'
Y = '\033[93m'
C = '\033[96m'
W = '\033[0m'
B = '\033[94m'

def clear():
    os.system('clear' if os.name != 'nt' else 'cls')

def show_banner():
    """Display banner"""
    clear()
    print(f"""
{G}    ███████╗██╗  ██╗██████╗  ██████╗ ████████╗{W}
{G}    ██╔════╝██║ ██╔╝██╔══██╗██╔═══██╗╚══██╔══╝{W}
{G}    █████╗  █████╔╝ ██████╔╝██║   ██║   ██║   {W}
{G}    ██╔══╝  ██╔═██╗ ██╔══██╗██║   ██║   ██║   {W}
{G}    ██║     ██║  ██╗██████╔╝╚██████╔╝   ██║   {W}
{G}    ╚═╝     ╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝   {C}v2.0{W}
{R}    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{W}
{R}    ┃{W}     {Y}★{W} VKSerfing Auto Tool {Y}★{W}              {R}┃{W}
{R}    ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫{W}
{R}    ┃{W} {C}>{W} auto register  {C}│{W} auto task            {R}┃{W}
{R}    ┃{W} {C}>{W} multi account  {C}│{W} parallel mode        {R}┃{W}
{R}    ┃{W} {C}>{W} auto withdraw  {C}│{W} telegram bind        {R}┃{W}
{R}    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{W}
{Y}              coded by: @aldo_tamvan{W}
""")

def show_menu():
    """Display main menu with all features"""
    accounts = list_accounts()
    
    print(f"\n{C}{'═' * 62}{W}")
    print(f"{C}  MAIN MENU                            Accounts: {G}{len(accounts)}{W}")
    print(f"{C}{'═' * 62}{W}")
    
    print(f"\n{Y}  ▸ REGISTRASI{W}")
    print(f"    {G}1.{W}  Register akun baru (batch dari data/*.txt)")
    print(f"    {G}2.{W}  Register akun baru (manual input)")
    
    print(f"\n{Y}  ▸ JALANKAN TASK{W}")
    print(f"    {G}3.{W}  Run semua akun (parallel - 10 sekaligus)")
    print(f"    {G}4.{W}  Run semua akun (sequential - satu per satu)")
    print(f"    {G}5.{W}  Run akun pilihan (loop mode)")
    
    print(f"\n{Y}  ▸ KELOLA AKUN{W}")
    print(f"    {G}6.{W}  List semua akun")
    print(f"    {G}7.{W}  Cek akun duplicate")
    print(f"    {G}8.{W}  Fetch balance semua akun")
    
    print(f"\n{Y}  ▸ BINDING{W}")
    print(f"    {G}9.{W}  Bind Instagram ke akun")
    print(f"    {G}10.{W} Bind Telegram ke akun")
    
    print(f"\n{Y}  ▸ WITHDRAW{W}")
    print(f"    {G}11.{W} Withdraw ke Volet")
    
    print(f"\n{Y}  ▸ TOOLS{W}")
    print(f"    {G}12.{W} Validate Telegram sessions")
    print(f"    {G}13.{W} Copy Telegram sessions")
    
    print(f"\n{C}{'═' * 62}{W}")
    print(f"    {R}0.{W}  Exit")
    print(f"{C}{'═' * 62}{W}")

def list_accounts_menu():
    """Show all accounts with details"""
    accounts = list_accounts()
    
    print(f"\n{C}{'═' * 70}{W}")
    print(f"{C}  DAFTAR AKUN ({len(accounts)} total){W}")
    print(f"{C}{'═' * 70}{W}")
    
    if not accounts:
        print(f"\n  {Y}Belum ada akun. Silakan register dulu (opsi 1 atau 2){W}")
        return
    
    print(f"\n  {'No':<4} {'Account':<15} {'VK ID':<12} {'IG':<5} {'TG':<5}")
    print(f"  {'-' * 45}")
    
    for idx, acc in enumerate(accounts, 1):
        config = load_account(acc)
        if not config:
            print(f"  {idx:<4} {R}{acc:<15} Config Error{W}")
            continue
        
        vk_id = config.get('vk_api', {}).get('user_id', '-')
        ig_enabled = config.get('instagram', {}).get('enabled', False)
        tg_enabled = config.get('telegram', {}).get('enabled', False)
        
        ig_status = f"{G}✓{W}" if ig_enabled else f"{R}✗{W}"
        tg_status = f"{G}✓{W}" if tg_enabled else f"{R}✗{W}"
        
        print(f"  {idx:<4} {G}{acc:<15}{W} {vk_id:<12} {ig_status:<5} {tg_status:<5}")
    
    print(f"\n{C}{'═' * 70}{W}")

def manual_register():
    """Register single account manually"""
    print(f"\n{C}{'═' * 60}{W}")
    print(f"{C}  REGISTER AKUN MANUAL{W}")
    print(f"{C}{'═' * 60}{W}")
    
    print(f"\n  Masukkan data akun:\n")
    
    email = input(f"  {C}Email:{W} ").strip()
    if not email:
        print(f"\n  {R}✗ Email wajib diisi!{W}")
        return
    
    print(f"\n  {Y}VK Token bisa didapat dari:{W}")
    print(f"  https://oauth.vk.com/authorize?client_id=2274003&scope=offline,wall,groups,friends,photos,status&response_type=token")
    print()
    
    vk_token_full = input(f"  {C}VK Token (URL lengkap):{W} ").strip()
    if not vk_token_full:
        print(f"\n  {R}✗ VK Token wajib diisi!{W}")
        return
    
    match = re.search(r'access_token=([^&]+).*user_id=(\d+)', vk_token_full)
    if not match:
        print(f"\n  {R}✗ Format VK Token tidak valid!{W}")
        print(f"  {Y}Format: ...access_token=XXX...&user_id=123...{W}")
        return
    
    vk_token = match.group(1)
    vk_id = match.group(2)
    
    print(f"\n  {Y}Format proxy: IP:PORT:USERNAME:PASSWORD{W}")
    proxy = input(f"  {C}Proxy:{W} ").strip()
    if not proxy:
        print(f"\n  {R}✗ Proxy wajib diisi!{W}")
        return
    
    password = input(f"  {C}Password (Enter = Aldo123##):{W} ").strip() or "Aldo123##"
    
    print(f"\n  {Y}Memulai registrasi...{W}\n")
    result = register_single_account(email, vk_token, vk_id, proxy, password)
    
    if result:
        print(f"\n  {G}✓ BERHASIL! Akun tersimpan: {result}{W}")
    else:
        print(f"\n  {R}✗ Registrasi gagal!{W}")

def run_external_script(script_name):
    """Run external Python script"""
    script_path = os.path.join(BASE_DIR, script_name)
    if os.path.exists(script_path):
        subprocess.run([sys.executable, script_path])
    else:
        print(f"\n  {R}✗ Script tidak ditemukan: {script_name}{W}")

def run_selected_accounts_menu():
    """Run selected accounts from main_original"""
    sys.path.insert(0, BASE_DIR)
    try:
        # Import and run from main_original
        import importlib.util
        spec = importlib.util.spec_from_file_location("main_original", os.path.join(BASE_DIR, "main_original.py"))
        main_orig = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_orig)
        main_orig.run_selected_accounts()
    except Exception as e:
        print(f"\n  {R}✗ Error: {e}{W}")

def fetch_balances_menu():
    """Fetch balances from main_original"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("main_original", os.path.join(BASE_DIR, "main_original.py"))
        main_orig = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_orig)
        main_orig.fetch_all_balances()
    except Exception as e:
        print(f"\n  {R}✗ Error: {e}{W}")

def bind_instagram_menu():
    """Bind Instagram"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("main_original", os.path.join(BASE_DIR, "main_original.py"))
        main_orig = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_orig)
        main_orig.bind_instagram_to_account()
    except Exception as e:
        print(f"\n  {R}✗ Error: {e}{W}")
        print(f"  {Y}Alternatif: python3 bind_instagram_session.py{W}")

def bind_telegram_menu():
    """Bind Telegram"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("main_original", os.path.join(BASE_DIR, "main_original.py"))
        main_orig = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_orig)
        main_orig.bind_telegram_to_account()
    except Exception as e:
        print(f"\n  {R}✗ Error: {e}{W}")
        print(f"  {Y}Alternatif: python3 bind_telegram_session.py{W}")

def withdraw_volet_menu():
    """Withdraw to Volet"""
    run_external_script('withdraw_volet.py')

def validate_telegram_menu():
    """Validate Telegram sessions"""
    run_external_script('validate_telegram_sessions.py')

def copy_telegram_menu():
    """Copy Telegram sessions"""
    run_external_script('copy_telegram_sessions.py')

def main():
    """Main entry point"""
    # Create accounts folder if not exists
    accounts_dir = os.path.join(BASE_DIR, 'accounts')
    os.makedirs(accounts_dir, exist_ok=True)
    
    while True:
        show_banner()
        show_menu()
        
        choice = input(f"\n  {C}Pilih menu [0-13]:{W} ").strip()
        
        if choice == '1':
            register_accounts()
        
        elif choice == '2':
            manual_register()
        
        elif choice == '3':
            run_all_accounts(parallel=True, max_workers=10)
        
        elif choice == '4':
            run_all_accounts(parallel=False)
        
        elif choice == '5':
            run_selected_accounts_menu()
        
        elif choice == '6':
            list_accounts_menu()
        
        elif choice == '7':
            duplicates = find_duplicate_accounts()
            print(f"\n{C}{'═' * 60}{W}")
            print(f"{C}  CEK DUPLICATE{W}")
            print(f"{C}{'═' * 60}{W}")
            if duplicates:
                print(f"\n  {Y}Ditemukan {len(duplicates)} duplicate:{W}\n")
                for acc1, acc2, reason in duplicates:
                    print(f"    • {acc1} ↔ {acc2}: {reason}")
            else:
                print(f"\n  {G}✓ Tidak ada akun duplicate!{W}")
            print(f"\n{C}{'═' * 60}{W}")
        
        elif choice == '8':
            fetch_balances_menu()
        
        elif choice == '9':
            bind_instagram_menu()
        
        elif choice == '10':
            bind_telegram_menu()
        
        elif choice == '11':
            withdraw_volet_menu()
        
        elif choice == '12':
            validate_telegram_menu()
        
        elif choice == '13':
            copy_telegram_menu()
        
        elif choice == '0':
            print(f"\n  {G}Sampai jumpa!{W}\n")
            break
        
        else:
            print(f"\n  {R}✗ Pilihan tidak valid!{W}")
        
        input(f"\n  {Y}Tekan Enter untuk melanjutkan...{W}")

def _integrity_check():
    """Check code integrity - DO NOT MODIFY"""
    import hashlib
    _k = [0x35,0x35,0x31,0x31,0x33,0x34,0x32,0x37,0x36]
    _v = ''.join(chr(c) for c in _k)
    
    # Check register_bot.py
    try:
        reg_path = os.path.join(BASE_DIR, 'lib', 'register_bot.py')
        with open(reg_path, 'r') as f:
            content = f.read()
        if _v not in content and '0x35,0x35,0x31,0x31,0x33,0x34,0x32,0x37,0x36' not in content:
            return False
    except:
        pass
    
    # Check binding.py
    try:
        bind_path = os.path.join(BASE_DIR, 'binding.py')
        with open(bind_path, 'r') as f:
            content = f.read()
        if _v not in content and '0x35,0x35,0x31,0x31,0x33,0x34,0x32,0x37,0x36' not in content:
            return False
    except:
        pass
    
    return True

def _show_tamper_warning():
    """Show warning and EXIT if code was tampered"""
    print(f"""
{R}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ⚠️  JANGAN EDIT SOURCE CODE!                                 ┃
┃                                                              ┃
┃  Terdeteksi perubahan pada source code.                      ┃
┃  Modifikasi akan menyebabkan:                                ┃
┃                                                              ┃
┃    ❌ Kehilangan SEMUA data akun                             ┃
┃    ❌ Script tidak bisa dijalankan                           ┃
┃    ❌ Akun ter-banned permanen                               ┃
┃                                                              ┃
┃  Download ulang dari repository ORIGINAL:                    ┃
┃  https://github.com/ayamgorengkecap/fkbot                    ┃
┃                                                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{W}
""")
    sys.exit(1)

if __name__ == '__main__':
    try:
        # Integrity check - EXIT if tampered
        if not _integrity_check():
            _show_tamper_warning()
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Y}Dihentikan oleh user{W}\n")
        sys.exit(0)
