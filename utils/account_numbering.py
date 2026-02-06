"""Safe account numbering to prevent overwrites"""
import os
import re

def get_next_account_number(accounts_dir='accounts'):
    """Get next safe account number using max-based algorithm"""
    if not os.path.exists(accounts_dir):
        return 1
    
    folders = [f for f in os.listdir(accounts_dir) 
               if os.path.isdir(os.path.join(accounts_dir, f)) and f.startswith('account_')]
    
    if not folders:
        return 1
    
    numbers = []
    for folder in folders:
        match = re.match(r'account_(\d+)', folder)
        if match:
            numbers.append(int(match.group(1)))
    
    return max(numbers) + 1 if numbers else 1

def parse_account_number(folder_name):
    """Extract number from account_N"""
    match = re.match(r'account_(\d+)', folder_name)
    return int(match.group(1)) if match else None
