"""Task execution module - WRAPPER ONLY
Calls original automation_core.py logic without modifications
"""
import sys
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'lib'))

from lib.automation_core import VKSerfingBot
from modules.accounts import list_accounts, load_account

G = '\033[92m'
R = '\033[91m'
Y = '\033[93m'
C = '\033[96m'
W = '\033[0m'

STOP_FLAG = False

def run_single_account(account_name):
    """Run tasks on single account using ORIGINAL automation_core.py"""
    try:
        config = load_account(account_name)
        if not config:
            return {'account': account_name, 'status': 'error', 'message': 'Failed to load config'}
        
        bot = VKSerfingBot(config, account_name)
        bot.run()
        
        return {
            'account': account_name,
            'status': 'success',
            'earned': getattr(bot, 'earned', 0),
            'balance': getattr(bot, 'balance', 0),
            'message': f"Earned {getattr(bot, 'earned', 0)}"
        }
        
    except Exception as e:
        return {
            'account': account_name,
            'status': 'error',
            'message': str(e)
        }

def run_all_accounts(parallel=True, max_workers=10):
    """Run tasks on all accounts - WRAPPER"""
    global STOP_FLAG
    
    print(f"\n{C}{'='*60}{W}")
    print(f"{C}🚀 TASK EXECUTION MODE{W}")
    print(f"{C}{'='*60}{W}")
    
    accounts = list_accounts()
    
    if not accounts:
        print(f"{R}❌ No accounts found!{W}")
        return {'success': [], 'failed': [], 'stats': {}}
    
    print(f"{G}✅ Found {len(accounts)} accounts{W}")
    
    results = []
    success = []
    failed = []
    
    if parallel:
        print(f"\n{C}[INFO] Running {len(accounts)} accounts in parallel (workers={max_workers}){W}\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(run_single_account, acc): acc for acc in accounts}
            
            done = 0
            for future in as_completed(futures):
                if STOP_FLAG:
                    break
                
                acc_name = futures[future]
                done += 1
                
                try:
                    result = future.result(timeout=300)
                    results.append(result)
                    
                    if result['status'] == 'success':
                        success.append(acc_name)
                        print(f"  [{done}/{len(accounts)}] {G}[OK]{W} {acc_name} - {result['message']}")
                    else:
                        failed.append(acc_name)
                        print(f"  [{done}/{len(accounts)}] {R}[FAIL]{W} {acc_name} - {result['message']}")
                        
                except Exception as e:
                    failed.append(acc_name)
                    print(f"  [{done}/{len(accounts)}] {R}[ERROR]{W} {acc_name} - {str(e)[:50]}")
    
    else:
        print(f"\n{C}[INFO] Running {len(accounts)} accounts sequentially{W}\n")
        
        for idx, acc in enumerate(accounts, 1):
            if STOP_FLAG:
                break
            
            print(f"\n{C}[{idx}/{len(accounts)}] Processing {acc}...{W}")
            result = run_single_account(acc)
            results.append(result)
            
            if result['status'] == 'success':
                success.append(acc)
                print(f"{G}✅ {result['message']}{W}")
            else:
                failed.append(acc)
                print(f"{R}❌ {result['message']}{W}")
    
    total_earned = sum(r.get('earned', 0) for r in results if r['status'] == 'success')
    total_balance = sum(r.get('balance', 0) for r in results if r['status'] == 'success')
    
    print(f"\n{C}{'='*60}{W}")
    print(f"{G}✅ TASKS COMPLETE{W}")
    print(f"{G}   Success: {len(success)}/{len(accounts)}{W}")
    print(f"{R}   Failed: {len(failed)}/{len(accounts)}{W}")
    print(f"{C}   Total earned: {total_earned}{W}")
    print(f"{C}   Total balance: {total_balance}{W}")
    print(f"{C}{'='*60}{W}")
    
    return {
        'success': success,
        'failed': failed,
        'stats': {
            'total_earned': total_earned,
            'total_balance': total_balance
        }
    }
