#!/usr/bin/env python3
"""
VKSerfing Volet Withdrawal Script
- Check balance semua akun (PARALLEL)
- Withdraw ke Volet wallet untuk balance >= 103₽
- Check withdrawal history
"""

import os
import json
import requests
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

ACCOUNTS_DIR = 'accounts'
MIN_WITHDRAW = 103
VOLET_FEE = 0.03
MAX_WORKERS = 10
WALLET_HISTORY_FILE = 'data/wallet_history.json'

G, R, Y, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[96m', '\033[0m'


def load_wallet_history():
    """Load wallet history from JSON file"""
    if os.path.exists(WALLET_HISTORY_FILE):
        try:
            with open(WALLET_HISTORY_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}


def save_wallet_history(history):
    """Save wallet history to JSON file"""
    os.makedirs(os.path.dirname(WALLET_HISTORY_FILE), exist_ok=True)
    with open(WALLET_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def get_account_wallet(account_name, history):
    """Get saved wallet for an account"""
    return history.get(account_name, {}).get('wallet')


def save_account_wallet(account_name, wallet, history):
    """Save wallet for an account"""
    if account_name not in history:
        history[account_name] = {}
    history[account_name]['wallet'] = wallet
    history[account_name]['last_used'] = __import__('time').strftime('%Y-%m-%d %H:%M:%S')
    save_wallet_history(history)


def parse_settings_html(html_content):
    """Parse email from /settings HTML"""
    import html as html_module
    
    email = None
    init_match = re.search(r':init-data="([^"]+)"', html_content)
    if init_match:
        try:
            init_str = html_module.unescape(init_match.group(1))
            init_data = json.loads(init_str)
            email = init_data.get('email')
        except:
            pass
    return email


def parse_proxy_string(proxy_str):
    """Parse proxy string to http://user:pass@ip:port format"""
    if not proxy_str:
        return None
    if proxy_str.startswith('http'):
        return proxy_str
    if proxy_str.count(':') == 3:
        parts = proxy_str.split(':')
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    if proxy_str.count(':') == 1:
        return f"http://{proxy_str}"
    return proxy_str


def get_session(config):
    """Create session with cookies and headers"""
    creds = config.get('credentials', {})
    cookies = creds.get('cookies', {})
    xsrf = creds.get('xsrf_token', '')
    proxy_str = config.get('proxy', {}).get('proxy_string', '')
    ua = config.get('user_agent', {}).get('user_agent', 'Mozilla/5.0 (Linux; Android 11) Chrome/131.0 Mobile Safari/537.36')

    s = requests.Session()
    s.cookies.update(cookies)
    s.headers.update({
        'User-Agent': ua,
        'X-XSRF-Token': xsrf,
        'X-Requested-With': 'XMLHttpRequest',
        'X-Ajax-Html': '1',
        'Accept': 'application/json, text/plain, */*',
    })

    if proxy_str:
        proxy = parse_proxy_string(proxy_str)
        if proxy:
            s.proxies = {'http': proxy, 'https': proxy}

    return s


def get_withdrawal_history(session, domain='https://vkserfing.com'):
    """
    Get withdrawal history from DUAL SOURCES:
    1. /notifications - for recent WD requests
    2. /cashout - for actual payment status (Выплачено/Не выплачено)
    
    ⚠️ CRITICAL: Notifications don't update after payment!
    Must check /cashout table for real status.
    """
    try:
        # Get balance and notifications
        r_notif = session.get(f'{domain}/notifications', timeout=15)
        if r_notif.status_code != 200:
            return 0.0, []
        
        resp_json = r_notif.json()
        html_notif = resp_json.get('html', '')
        balance = float(resp_json.get('data', {}).get('balance', '0'))
        
        # Get cashout page for actual status
        r_cashout = session.get(f'{domain}/cashout', timeout=15)
        html_cashout = ''
        if r_cashout.status_code == 200:
            html_cashout = r_cashout.json().get('html', '')
        
        # Parse notifications for WD list
        pattern = r'<div class="notify notify--(\w+)\s*([^"]*)">\s*<span class="notify__text">\s*(.*?)\s*</span>\s*<span class="notify__time">(.*?)</span>'
        matches = re.findall(pattern, html_notif, re.DOTALL)
        
        withdrawals = []
        
        for notify_type, extra_class, text, time in matches:
            text_clean = re.sub(r'<[^>]+>', '', text).strip()
            text_clean = re.sub(r'\s+', ' ', text_clean)
            
            # Filter: only real WD events
            if not ('вывод' in text_clean.lower() and ('сумму' in text_clean.lower() or 'выведены' in text_clean.lower())):
                continue
            
            # Extract amount
            amount_match = re.search(r'<b>(\d+)</b>\s*₽', text)
            amount = amount_match.group(1) if amount_match else '0'
            
            if amount == '0':
                continue
            
            # Extract method
            method_match = re.search(r'на\s*<b>([^<]+)</b>', text)
            method = method_match.group(1).strip() if method_match else 'Unknown'
            
            # Extract date for matching with cashout table
            date_str = time.strip()
            
            # Translate Russian date to English
            date_str = date_str.replace('января', 'Jan').replace('февраля', 'Feb').replace('марта', 'Mar')
            date_str = date_str.replace('апреля', 'Apr').replace('мая', 'May').replace('июня', 'Jun')
            date_str = date_str.replace('июля', 'Jul').replace('августа', 'Aug').replace('сентября', 'Sep')
            date_str = date_str.replace('октября', 'Oct').replace('ноября', 'Nov').replace('декабря', 'Dec')
            date_str = date_str.replace('в', 'at').replace('часов назад', 'hours ago').replace('час назад', 'hour ago')
            date_str = date_str.replace('минут назад', 'min ago').replace('только что', 'just now')
            date_str = date_str.replace('вчера', 'yesterday').replace('сегодня', 'today')
            
            # Initial status from notification text
            if 'Создан запрос на вывод' in text_clean:
                status = 'Pending'
            elif 'Средства выведены' in text_clean or 'выплачено' in text_clean.lower():
                status = 'Paid'
            elif 'отклонен' in text_clean.lower() or 'отказ' in text_clean.lower():
                status = 'Rejected'
            else:
                status = 'Unknown'
            
            # Cross-check with /cashout table for real status
            if html_cashout and amount != '0':
                # Parse cashout table items
                cashout_items = re.findall(r'<tr is="cashout-item"[^>]*>.*?</tr>', html_cashout, re.DOTALL)
                
                for item_html in cashout_items:
                    # Check if this item matches our amount
                    item_amount_match = re.search(r'<span class="text-style">(\d+)\s*₽</span>', item_html)
                    if item_amount_match and item_amount_match.group(1) == amount:
                        # Found matching amount, check status
                        if 'Выплачено' in item_html:  # Paid
                            status = 'Paid'  # Override
                            break
                        elif 'Не выплачено' in item_html:  # Not paid
                            status = 'Pending'
                            break
            
            withdrawals.append({
                'amount': amount,
                'method': method,
                'date': date_str,
                'status': status,
                'text': text_clean,
                'is_new': 'notify--new' in extra_class
            })
        
        return balance, withdrawals
    except Exception as e:
        pass
    return 0.0, []


def get_balance(session, domain='https://vkserfing.com'):
    """Get balance from /cashout or /notifications"""
    try:
        r = session.get(f'{domain}/cashout', timeout=15)
        if r.status_code == 200:
            data = r.json().get('data', {})
            balance = data.get('balance', '0')
            return float(balance)
    except:
        pass


    try:
        r = session.get(f'{domain}/notifications', timeout=15)
        if r.status_code == 200:
            data = r.json().get('data', {})
            balance = data.get('balance', '0')
            return float(balance)
    except:
        pass

    return 0.0


def withdraw_volet(session, wallet, amount, domain='https://vkserfing.com'):
    """
    Withdraw to Volet wallet
    wallet format: "U 9148 5460 4126"
    amount: integer (rounded down from balance)
    """
    payload = {
        "bill": wallet,
        "amount": amount,
        "type": "volet"
    }

    try:
        headers = dict(session.headers)
        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json, text/plain, */*'
        # Keep X-Ajax-Html for proper response format
        headers['X-Ajax-Html'] = '1'

        r = session.post(f'{domain}/cashout', json=payload, headers=headers, timeout=15)

        if 'заблокирован' in r.text.lower() or ('<html' in r.text.lower() and 'blocked' in r.text.lower()):
            return False, 'BANNED', 0

        try:
            data = r.json()
        except:
            print(f"\n{Y}[DEBUG] Raw response: {r.text[:200]}{W}")
            return False, 'Invalid response', 0

        # Check for success - either by status field or by message in data
        if data.get('status') == 'success':
            msg = data.get('data', {}).get('message', 'Success')
            new_balance = data.get('data', {}).get('balance', '0')
            return True, msg, float(new_balance)
        
        # Alternative success detection: check if data.message contains success text
        data_inner = data.get('data', {})
        msg = data_inner.get('message', '')
        if msg and ('оформлен' in msg.lower() or 'выплат' in msg.lower()):
            new_balance = data_inner.get('balance', '0')
            return True, msg, float(new_balance)
        
        # Failed - extract error message
        error = data.get('message') or data_inner.get('message') or f'Unknown: {str(data)[:100]}'
        return False, error, 0
    except Exception as e:
        return False, f'Exception: {str(e)[:50]}', 0


def get_account_folders():
    """Get all account folders"""
    if not os.path.exists(ACCOUNTS_DIR):
        return []
    folders = []
    for f in os.listdir(ACCOUNTS_DIR):
        if f.startswith('account_') and os.path.isdir(os.path.join(ACCOUNTS_DIR, f)):
            folders.append(f)

    folders.sort(key=lambda x: int(x.split('_')[1]) if x.split('_')[1].isdigit() else 0)
    return folders


def input_wallets():
    """Input Volet wallets"""
    print(f"\n{C}=== Input Volet Wallets ==={W}")
    print(f"Format: U XXXX XXXX XXXX")
    print(f"Enter one wallet per line, empty line to finish")
    print(f"Or paste multiple wallets at once\n")

    wallets = []
    while True:
        try:
            line = input(f"{Y}Wallet [{len(wallets)+1}]: {W}").strip()
            if not line:
                if wallets:
                    break
                print(f"{R}Enter at least one wallet{W}")
                continue


            if re.match(r'^U\s*\d{4}\s*\d{4}\s*\d{4}$', line):

                nums = re.findall(r'\d{4}', line)
                wallet = f"U {nums[0]} {nums[1]} {nums[2]}"
                wallets.append(wallet)
                print(f"{G}  ✓ Added: {wallet}{W}")
            else:
                print(f"{R}  ✗ Invalid format. Use: U XXXX XXXX XXXX{W}")
        except EOFError:
            break
        except KeyboardInterrupt:
            print(f"\n{Y}Cancelled{W}")
            return []

    return wallets


def input_single_wallet(account_name):
    """Input single wallet for an account"""
    while True:
        line = input(f"  {Y}Input wallet untuk {account_name} (U XXXX XXXX XXXX): {W}").strip()
        if not line:
            return None
        if re.match(r'^U\s*\d{4}\s*\d{4}\s*\d{4}$', line):
            nums = re.findall(r'\d{4}', line)
            return f"U {nums[0]} {nums[1]} {nums[2]}"
        print(f"  {R}Format tidak valid! Gunakan: U XXXX XXXX XXXX{W}")


def main():
    print(f"\n{C}{'='*60}{W}")
    print(f"{C}  VKSerfing Volet Withdrawal Tool{W}")
    print(f"{C}{'='*60}{W}")

    # Load wallet history
    wallet_history = load_wallet_history()
    
    # Get account folders first
    folders = get_account_folders()
    if not folders:
        print(f"{R}No accounts found in {ACCOUNTS_DIR}/{W}")
        return

    print(f"\n{C}Checking {len(folders)} accounts (parallel)...{W}\n")

    def check_balance_single(folder):
        config_path = os.path.join(ACCOUNTS_DIR, folder, 'config.json')
        if not os.path.exists(config_path):
            return {'folder': folder, 'status': 'error', 'error': 'no config'}
        try:
            with open(config_path) as f:
                config = json.load(f)
            session = get_session(config)
            balance = get_balance(session)
            return {'folder': folder, 'balance': balance, 'config': config, 'status': 'ok'}
        except Exception as e:
            return {'folder': folder, 'status': 'error', 'error': str(e)[:30]}

    eligible = []
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_balance_single, f): f for f in folders}
        done = 0
        total = len(futures)

        for future in as_completed(futures):
            done += 1
            print(f"\r  Scanning... [{done}/{total}]", end="", flush=True)
            try:
                result = future.result(timeout=20)
                results.append(result)
            except:
                results.append({'folder': futures[future], 'status': 'error', 'error': 'timeout'})

    print(f"\r  Scanning... [{total}/{total}] Done!{' '*20}\n")

    # Check eligible accounts and show wallet history status
    for r in sorted(results, key=lambda x: int(x['folder'].split('_')[1]) if '_' in x['folder'] else 0):
        if r['status'] == 'error':
            print(f"  {r['folder']}: {R}Error - {r.get('error', 'unknown')}{W}")
        else:
            balance = r['balance']
            saved_wallet = get_account_wallet(r['folder'], wallet_history)
            wallet_status = f"{C}[{saved_wallet}]{W}" if saved_wallet else f"{Y}[NEW]{W}"
            
            if balance >= MIN_WITHDRAW:
                eligible.append(r)
                print(f"  {r['folder']}: {balance:.2f}₽ {G}✓ ELIGIBLE{W} {wallet_status}")
            else:
                print(f"  {r['folder']}: {balance:.2f}₽ {Y}skip{W}")

    if not eligible:
        print(f"\n{Y}No accounts with balance >= {MIN_WITHDRAW}₽{W}")
        return

    # Count accounts with/without saved wallet
    with_wallet = sum(1 for a in eligible if get_account_wallet(a['folder'], wallet_history))
    without_wallet = len(eligible) - with_wallet

    total_balance = sum(a['balance'] for a in eligible)
    total_withdraw = sum(int(a['balance']) for a in eligible)
    total_receive = total_withdraw * (1 - VOLET_FEE)

    print(f"\n{C}{'='*60}{W}")
    print(f"{G}Eligible accounts: {len(eligible)}{W}")
    print(f"{C}  - Dengan wallet tersimpan: {with_wallet}{W}")
    print(f"{Y}  - Akun baru (perlu input wallet): {without_wallet}{W}")
    print(f"{G}Total balance: {total_balance:.2f}₽{W}")
    print(f"{G}Total to withdraw: {total_withdraw}₽{W}")
    print(f"{G}After 3% fee: ~{total_receive:.2f}₽{W}")
    print(f"{C}{'='*60}{W}")

    # Ask wallet mode
    print(f"\n{C}Pilih mode wallet:{W}")
    print(f"  {G}1.{W} Gunakan wallet history (akun lama) + input manual (akun baru)")
    print(f"  {G}2.{W} Input wallet baru untuk SEMUA akun (batch mode lama)")
    print(f"  {G}3.{W} Gunakan 1 wallet untuk SEMUA akun")
    
    mode = input(f"\n{Y}Pilih mode [1/2/3]: {W}").strip()
    
    if mode == '2':
        # Old batch mode - input wallets manually
        wallets = input_wallets()
        if not wallets:
            print(f"{R}No wallets provided. Exiting.{W}")
            return
        use_history = False
        single_wallet = None
        
    elif mode == '3':
        # Single wallet for all
        print(f"\n{C}Input 1 wallet untuk semua akun:{W}")
        single_wallet = input_single_wallet("SEMUA")
        if not single_wallet:
            print(f"{R}No wallet provided. Exiting.{W}")
            return
        wallets = [single_wallet]
        use_history = False
        
    else:
        # Mode 1: Use history + input for new accounts
        use_history = True
        wallets = []
        single_wallet = None

    confirm = input(f"\n{Y}Proceed with withdrawal? (yes/no): {W}").strip().lower()
    if confirm not in ['yes', 'y']:
        print(f"{Y}Cancelled{W}")
        return

    print(f"\n{C}Processing withdrawals...{W}\n")

    wallet_idx = 0
    success_count = 0
    total_withdrawn = 0

    for acc in eligible:
        folder = acc['folder']
        config = acc['config']

        try:
            session = get_session(config)

            # Check balance FIRST before asking for wallet
            balance = get_balance(session)
            if balance < MIN_WITHDRAW:
                print(f"  {folder}: {balance:.2f}₽ {Y}skip (below min){W}")
                continue

            # Determine wallet to use (only after confirming balance is enough)
            if use_history:
                saved_wallet = get_account_wallet(folder, wallet_history)
                if saved_wallet:
                    wallet = saved_wallet
                    print(f"  {folder}: Menggunakan wallet tersimpan: {C}{wallet}{W}")
                else:
                    # New account - need to input wallet
                    print(f"\n  {Y}[NEW ACCOUNT] {folder} ({balance:.2f}₽) belum punya wallet tersimpan{W}")
                    wallet = input_single_wallet(folder)
                    if not wallet:
                        print(f"  {Y}Skipped (no wallet){W}")
                        continue
            elif single_wallet:
                wallet = single_wallet
            else:
                wallet = wallets[wallet_idx % len(wallets)]
                wallet_idx += 1

            amount = int(balance)
            print(f"  {folder}: {balance:.2f}₽ → {amount}₽ to {wallet}...", end=" ", flush=True)

            success, msg, _ = withdraw_volet(session, wallet, amount)

            if success:
                print(f"{G}✓ {msg}{W}")
                
                # Save wallet to history on successful withdrawal
                save_account_wallet(folder, wallet, wallet_history)

                import time
                time.sleep(5)
                new_balance = get_balance(session)
                print(f"       → Remaining: {new_balance:.2f}₽")
                success_count += 1
                total_withdrawn += amount
            else:
                print(f"{R}✗ {msg}{W}")
        except Exception as e:
            print(f"{R}✗ Error: {str(e)[:30]}{W}")

    print(f"\n{C}{'='*60}{W}")
    print(f"{G}Completed: {success_count}/{len(eligible)} accounts{W}")
    print(f"{G}Total withdrawn: {total_withdrawn}₽{W}")
    print(f"{G}Expected receive: ~{total_withdrawn * (1 - VOLET_FEE):.2f}₽{W}")
    print(f"{C}{'='*60}{W}")


def check_history():
    """Check withdrawal history for all accounts (PARALLEL)"""
    print(f"\n{C}{'='*60}{W}")
    print(f"{C}  Withdrawal History Check{W}")
    print(f"{C}{'='*60}{W}")

    folders = get_account_folders()
    if not folders:
        print(f"{R}No accounts found{W}")
        return

    print(f"\n{C}Checking {len(folders)} accounts (parallel)...{W}\n")

    def check_history_single(folder):
        config_path = os.path.join(ACCOUNTS_DIR, folder, 'config.json')
        if not os.path.exists(config_path):
            return {'folder': folder, 'status': 'error'}
        try:
            with open(config_path) as f:
                config = json.load(f)
            session = get_session(config)
            balance, withdrawals = get_withdrawal_history(session)
            
            # Fetch email from /settings
            email = '-'
            try:
                resp = session.get('https://vkserfing.com/settings', timeout=10)
                if resp.status_code == 200:
                    html = resp.json().get('html', '')
                    email = parse_settings_html(html) or '-'
            except:
                pass
            
            # Separate by status
            pending = [w for w in withdrawals if w['status'] == 'Pending']
            paid = [w for w in withdrawals if w['status'] == 'Paid']
            rejected = [w for w in withdrawals if w['status'] == 'Rejected']
            
            return {
                'folder': folder, 
                'email': email,
                'balance': balance, 
                'pending': pending,
                'paid': paid,
                'rejected': rejected,
                'status': 'ok'
            }
        except:
            return {'folder': folder, 'status': 'error'}

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_history_single, f): f for f in folders}
        done = 0
        total = len(futures)

        for future in as_completed(futures):
            done += 1
            print(f"\r  Scanning... [{done}/{total}]", end="", flush=True)
            try:
                results.append(future.result(timeout=20))
            except:
                results.append({'folder': futures[future], 'status': 'error'})

    print(f"\r  Scanning... [{total}/{total}] Done!{' '*20}\n")

    # Collect all data
    accounts_with_wd = []
    total_pending = 0
    total_pending_amount = 0
    total_paid = 0
    total_paid_amount = 0
    error_count = 0

    for r in sorted(results, key=lambda x: int(x['folder'].split('_')[1]) if '_' in x['folder'] else 0):
        if r['status'] == 'error':
            error_count += 1
            continue

        has_wd = r.get('pending') or r.get('paid') or r.get('rejected')
        
        if has_wd:
            for w in r.get('pending', []):
                total_pending += 1
                total_pending_amount += int(w['amount'])
            
            for w in r.get('paid', []):
                total_paid += 1
                total_paid_amount += int(w['amount'])
            
            accounts_with_wd.append(r)
    
    # Print table header
    print(f"{C}{'='*120}{W}")
    print(f"{C}{'Account':<15} {'Email':<30} {'Balance':>10} {'Status':>8} {'Amount':>8} {'Date':<25}{W}")
    print(f"{C}{'-'*120}{W}")
    
    # Print table rows
    for r in accounts_with_wd:
        account = r['folder']
        email = r.get('email', '-')[:28]  # Truncate long emails
        balance = f"{r['balance']:.2f}₽"
        
        # Print pending
        for w in r.get('pending', []):
            status = f"{Y}PENDING{W}"
            amount = f"{w['amount']}₽"
            date = w['date']
            print(f"{account:<15} {email:<30} {balance:>10} {status:>8} {amount:>8} {date:<25}")
            account = ""  # Only show account name once
            email = ""
            balance = ""
        
        # Print paid
        for w in r.get('paid', []):
            status = f"{G}PAID{W}"
            amount = f"{w['amount']}₽"
            date = w['date']
            print(f"{account:<15} {email:<30} {balance:>10} {status:>8} {amount:>8} {date:<25}")
            account = ""
            email = ""
            balance = ""
        
        # Print rejected
        for w in r.get('rejected', []):
            status = f"{R}REJECTED{W}"
            amount = f"{w['amount']}₽"
            date = w['date']
            print(f"{account:<15} {email:<30} {balance:>10} {status:>8} {amount:>8} {date:<25}")
            account = ""
            email = ""
            balance = ""

    print(f"{C}{'='*120}{W}")
    print(f"{Y}PENDING: {total_pending} withdrawals | {total_pending_amount}₽{W}")
    print(f"{G}PAID:    {total_paid} withdrawals | {total_paid_amount}₽{W}")
    if error_count > 0:
        print(f"{R}ERRORS:  {error_count} accounts (proxy/connection issues){W}")
    print(f"{C}{'='*100}{W}")
    
    # Show wallet history for PAID withdrawals
    if total_paid > 0:
        print(f"\n{C}Show wallet addresses for PAID withdrawals? (y/n):{W} ", end='')
        show_wallets = input().strip().lower()
        
        if show_wallets == 'y':
            print(f"\n{C}{'='*80}{W}")
            print(f"{C}PAID Withdrawal Wallet History{W}")
            print(f"{C}{'='*80}{W}\n")
            
            # Get wallet info from cashout page
            print(f"{C}Fetching wallet details...{W}\n")
            
            wallet_history = {}
            
            for r in accounts_with_wd:
                if not r.get('paid'):
                    continue
                
                account = r['folder']
                config_path = os.path.join(ACCOUNTS_DIR, account, 'config.json')
                
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                    
                    session = get_session(config)
                    resp = session.get('https://vkserfing.com/cashout', timeout=15)
                    
                    if resp.status_code == 200:
                        html = resp.json().get('html', '')
                        
                        # Parse cashout items for wallet addresses
                        items = re.findall(r'<tr is="cashout-item"[^>]*>.*?</tr>', html, re.DOTALL)
                        
                        for item in items:
                            # Check if paid
                            if 'Выплачено' not in item:
                                continue
                            
                            # Extract amount
                            amount_match = re.search(r'<span class="text-style">(\d+)\s*₽</span>', item)
                            if not amount_match:
                                continue
                            
                            amount = amount_match.group(1)
                            
                            # Check if this amount is in our paid list
                            is_our_wd = any(w['amount'] == amount for w in r['paid'])
                            if not is_our_wd:
                                continue
                            
                            # Extract wallet
                            wallet_match = re.search(r'word-break-all[^>]*>([^<]+)</div>', item)
                            if wallet_match:
                                wallet = wallet_match.group(1).strip()
                                
                                # Extract date
                                date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', item)
                                date = date_match.group(1) if date_match else 'Unknown'
                                
                                if wallet not in wallet_history:
                                    wallet_history[wallet] = {
                                        'count': 0,
                                        'total': 0,
                                        'accounts': set(),
                                        'dates': []
                                    }
                                
                                wallet_history[wallet]['count'] += 1
                                wallet_history[wallet]['total'] += int(amount)
                                wallet_history[wallet]['accounts'].add(account)
                                wallet_history[wallet]['dates'].append(f"{amount}₽ on {date}")
                except:
                    pass
            
            # Display wallet summary and auto-save
            if wallet_history:
                saved_history = load_wallet_history()
                newly_saved = 0
                
                for wallet, info in wallet_history.items():
                    print(f"{G}Wallet:{W} {C}{wallet}{W}")
                    print(f"  Total PAID: {info['count']} withdrawals | {info['total']}₽")
                    print(f"  Accounts: {', '.join(sorted(info['accounts']))}")
                    print(f"  History:")
                    for h in info['dates']:
                        print(f"    - {h}")
                    
                    # Auto-save wallet for accounts that don't have saved wallet yet
                    for account in info['accounts']:
                        if account not in saved_history:
                            save_account_wallet(account, wallet, saved_history)
                            newly_saved += 1
                            print(f"  {G}✓ Auto-saved wallet for {account}{W}")
                    
                    print()
                
                if newly_saved > 0:
                    print(f"\n{G}✓ {newly_saved} wallet(s) auto-saved ke history!{W}")
            else:
                print(f"{Y}No wallet details found{W}\n")
            
            print(f"{C}{'='*80}{W}")


def manage_wallet_history():
    """Manage saved wallet history"""
    print(f"\n{C}{'='*60}{W}")
    print(f"{C}  Wallet History Manager{W}")
    print(f"{C}{'='*60}{W}")
    
    history = load_wallet_history()
    
    if not history:
        print(f"\n{Y}Belum ada wallet tersimpan.{W}")
        print(f"{Y}Wallet akan otomatis tersimpan saat WD berhasil.{W}")
        return
    
    print(f"\n{G}Saved Wallets ({len(history)} accounts):{W}\n")
    print(f"  {'Account':<15} {'Wallet':<20} {'Last Used':<20}")
    print(f"  {'-'*55}")
    
    for account, data in sorted(history.items()):
        wallet = data.get('wallet', '-')
        last_used = data.get('last_used', '-')
        print(f"  {account:<15} {C}{wallet:<20}{W} {last_used:<20}")
    
    print(f"\n{C}{'='*60}{W}")
    print(f"  {G}1.{W} Edit wallet untuk akun tertentu")
    print(f"  {G}2.{W} Hapus wallet untuk akun tertentu")
    print(f"  {G}3.{W} Hapus SEMUA wallet history")
    print(f"  {G}0.{W} Kembali")
    print(f"{C}{'='*60}{W}")
    
    choice = input(f"\n{Y}Pilih opsi: {W}").strip()
    
    if choice == '1':
        account = input(f"{Y}Nama akun (e.g. account_1): {W}").strip()
        if account:
            new_wallet = input_single_wallet(account)
            if new_wallet:
                save_account_wallet(account, new_wallet, history)
                print(f"{G}✓ Wallet untuk {account} diupdate ke {new_wallet}{W}")
    
    elif choice == '2':
        account = input(f"{Y}Nama akun yang akan dihapus: {W}").strip()
        if account in history:
            del history[account]
            save_wallet_history(history)
            print(f"{G}✓ Wallet untuk {account} dihapus{W}")
        else:
            print(f"{R}Akun tidak ditemukan{W}")
    
    elif choice == '3':
        confirm = input(f"{R}Yakin hapus SEMUA wallet history? (yes/no): {W}").strip().lower()
        if confirm in ['yes', 'y']:
            save_wallet_history({})
            print(f"{G}✓ Semua wallet history dihapus{W}")


def show_menu():
    """Show main menu"""
    history = load_wallet_history()
    wallet_count = len(history)
    
    print(f"\n{C}{'='*60}{W}")
    print(f"{C}  VKSerfing Volet Tool{W}")
    print(f"{C}{'='*60}{W}")
    print(f"  {G}1.{W} Withdraw to Volet")
    print(f"  {G}2.{W} Check withdrawal history")
    print(f"  {G}3.{W} Kelola wallet history {C}[{wallet_count} wallets tersimpan]{W}")
    print(f"  {R}0.{W} Exit")
    print(f"{C}{'='*60}{W}")
    return input(f"{Y}Select option: {W}").strip()


if __name__ == '__main__':
    while True:
        choice = show_menu()
        if choice == '1':
            main()
        elif choice == '2':
            check_history()
        elif choice == '3':
            manage_wallet_history()
        elif choice == '0':
            print(f"{G}Bye!{W}")
            break
        else:
            print(f"{R}Invalid option{W}")
