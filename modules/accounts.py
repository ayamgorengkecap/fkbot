"""Account management module - WRAPPER ONLY, NO LOGIC CHANGES"""
import os
import json
import sys
import fcntl
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'utils'))

from utils.account_numbering import get_next_account_number
from utils.config_loader import load_config, save_config

ACCOUNTS_DIR = BASE_DIR / "accounts"
LOCK_FILE = BASE_DIR / "data" / ".accounts.lock"

def list_accounts():
    """List all account folders"""
    if not ACCOUNTS_DIR.exists():
        return []
    
    folders = [f.name for f in ACCOUNTS_DIR.iterdir() 
               if f.is_dir() and f.name.startswith('account_') 
               and (f / 'config.json').exists()]
    
    return sorted(folders, key=lambda x: int(x.split('_')[1]) if '_' in x and x.split('_')[1].isdigit() else 0)

def load_account(account_name):
    """Load account config"""
    config_path = ACCOUNTS_DIR / account_name / 'config.json'
    return load_config(str(config_path))

def save_account(account_name, config, overwrite=False):
    """Save account config safely"""
    account_dir = ACCOUNTS_DIR / account_name
    config_file = account_dir / 'config.json'
    
    if config_file.exists() and not overwrite:
        raise ValueError(f"Account {account_name} already exists! Use overwrite=True to force.")
    
    account_dir.mkdir(parents=True, exist_ok=True)
    save_config(str(config_file), config)
    return True

def _acquire_lock():
    """Acquire file lock to prevent race conditions"""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(LOCK_FILE, 'w')
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd
    except BlockingIOError:
        # Wait and retry
        print("⏳ Waiting for lock...")
        fcntl.flock(lock_fd, fcntl.LOCK_EX)  # Blocking wait
        return lock_fd


def _release_lock(lock_fd):
    """Release file lock"""
    if lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


def check_duplicate_vk_id(vk_id):
    """Check if VK ID already exists"""
    if not vk_id:
        return None
    for acc in list_accounts():
        existing = load_account(acc)
        if existing:
            existing_vk_id = existing.get('vk_api', {}).get('user_id') or existing.get('vk', {}).get('user_id')
            if existing_vk_id and str(existing_vk_id) == str(vk_id):
                return acc
    return None


def check_duplicate_email(email):
    """Check if email already exists in any account"""
    if not email:
        return None
    email_lower = email.lower().strip()
    for acc in list_accounts():
        existing = load_account(acc)
        if existing:
            # Check multiple possible email locations
            existing_email = (
                existing.get('email') or 
                existing.get('credentials', {}).get('email') or
                existing.get('init_data', {}).get('email') or
                ''
            ).lower().strip()
            if existing_email and existing_email == email_lower:
                return acc
    return None


def create_new_account(config, email=None):
    """Create new account with safe numbering - checks for duplicates
    
    Args:
        config: Account configuration dict
        email: Optional email for duplicate checking (recommended)
    
    Returns:
        account_name if successful, None if duplicate found
    """
    lock_fd = None
    try:
        # Acquire lock to prevent race conditions
        lock_fd = _acquire_lock()
        
        ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Check duplicate VK ID
        vk_id = config.get('vk_api', {}).get('user_id') or config.get('vk', {}).get('user_id')
        if vk_id:
            existing_acc = check_duplicate_vk_id(vk_id)
            if existing_acc:
                print(f"⚠️  Account with VK ID {vk_id} already exists: {existing_acc}")
                print(f"   Skipping to prevent duplicate...")
                return None
        
        # Check duplicate email
        if email:
            existing_acc = check_duplicate_email(email)
            if existing_acc:
                print(f"⚠️  Account with email {email} already exists: {existing_acc}")
                print(f"   Skipping to prevent duplicate...")
                return None
        
        # Store email in config for future duplicate checks
        if email and 'email' not in config:
            config['email'] = email
        
        # Get next safe account number (with lock, this is now atomic)
        account_num = get_next_account_number(str(ACCOUNTS_DIR))
        account_name = f"account_{account_num}"
        
        # Double-check the folder doesn't exist (extra safety)
        account_path = ACCOUNTS_DIR / account_name
        if account_path.exists():
            print(f"⚠️  Race condition detected! {account_name} already exists")
            # Find next available
            while account_path.exists():
                account_num += 1
                account_name = f"account_{account_num}"
                account_path = ACCOUNTS_DIR / account_name
        
        save_account(account_name, config, overwrite=False)
        return account_name
        
    finally:
        _release_lock(lock_fd)

def find_duplicate_accounts():
    """Find accounts with same VK ID or email"""
    accounts = list_accounts()
    duplicates = []
    
    for i, acc1 in enumerate(accounts):
        config1 = load_account(acc1)
        if not config1:
            continue
        
        for acc2 in accounts[i+1:]:
            config2 = load_account(acc2)
            if not config2:
                continue
            
            # Check duplicate VK ID
            vk1_id = config1.get('vk_api', {}).get('user_id') or config1.get('vk', {}).get('user_id')
            vk2_id = config2.get('vk_api', {}).get('user_id') or config2.get('vk', {}).get('user_id')
            if vk1_id and vk2_id and str(vk1_id) == str(vk2_id):
                duplicates.append((acc1, acc2, f'Same VK ID: {vk1_id}'))
            
            # Check duplicate email
            email1 = (
                config1.get('email') or 
                config1.get('credentials', {}).get('email') or
                config1.get('init_data', {}).get('email') or
                ''
            ).lower().strip()
            email2 = (
                config2.get('email') or 
                config2.get('credentials', {}).get('email') or
                config2.get('init_data', {}).get('email') or
                ''
            ).lower().strip()
            if email1 and email2 and email1 == email2:
                duplicates.append((acc1, acc2, f'Same Email: {email1}'))
    
    return duplicates
