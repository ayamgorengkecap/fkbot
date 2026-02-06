# VKSerbot Unified v2 - Architecture

## Diagram Alur Eksekusi

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                    (UNIFIED ENTRY POINT)                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Menu Option 1│  │ Menu Option 3│  │ Menu Option 7│       │
│  │   Register   │  │  Run Tasks   │  │   Original   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ modules/        │  │ modules/        │  │ main_original.py│
│ register.py     │  │ tasks.py        │  │ (FULL FEATURES) │
│ (WRAPPER)       │  │ (WRAPPER)       │  │                 │
└────────┬────────┘  └────────┬────────┘  └─────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                         lib/                                 │
│              (LOGIKA ASLI - TIDAK DIUBAH)                   │
│                                                              │
│  ┌─────────────────┐       ┌─────────────────┐              │
│  │ register_bot.py │       │ automation_core │              │
│  │                 │       │     .py         │              │
│  │ - VKSerfingBot  │       │ - VKSerfingBot  │              │
│  │ - VKManager     │       │ - Colors        │              │
│  │ - _solve_captcha│       │ - run()         │              │
│  │ - register()    │       │ - get_tasks()   │              │
│  │ - bind_vk()     │       │ - execute_task()│              │
│  └────────┬────────┘       └────────┬────────┘              │
│           │                         │                        │
│           ▼                         ▼                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              vk_api_wrapper.py                      │    │
│  │           proxy_manager.py                          │    │
│  │           telegram_wrapper.py                       │    │
│  │           (SUPPORTING MODULES)                      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       accounts/                              │
│               (SHARED STORAGE - COMPATIBLE)                  │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ account_1/      │  │ account_2/      │  ...              │
│  │ └── config.json │  │ └── config.json │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                              │
│  FORMAT (SAMA untuk register & task):                       │
│  {                                                           │
│    "proxy": {...},                                           │
│    "credentials": {"cookies": {...}, "xsrf_token": "..."},  │
│    "vk_api": {"enabled": true, "user_id": "...", ...},      │
│    "instagram": {...},                                       │
│    "telegram": {...}                                         │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

## Prinsip Integrasi

### 1. TIDAK ADA PERUBAHAN LOGIKA
- `lib/register_bot.py` = KODE ASLI vkservtermux
- `lib/automation_core.py` = KODE ASLI vkserbot.v2
- HANYA tambah wrapper layer di `modules/`

### 2. WRAPPER PATTERN
```python
# modules/register.py
from lib.register_bot import VKSerfingBot as VKSerfingRegisterBot

def register_single_account(...):
    bot = VKSerfingRegisterBot(proxy)  # Panggil kelas ASLI
    bot.register(...)                   # Method ASLI
    bot.bind_vk(...)                    # Method ASLI
    # Hanya bungkus hasil ke format yang benar
```

### 3. DUPLICATE CHECK
```python
# modules/accounts.py
def create_new_account(config):
    # CEK DUPLICATE sebelum simpan
    vk_id = config.get('vk_api', {}).get('user_id')
    for acc in list_accounts():
        existing = load_account(acc)
        if existing.get('vk_api', {}).get('user_id') == vk_id:
            return None  # SKIP - jangan overwrite
    
    # Buat baru dengan nomor aman
    account_num = get_next_account_number()
    # ...
```

## Flow Register → Task

```
1. User input: email, vk_token, proxy
                    │
                    ▼
2. modules/register.py (WRAPPER)
   ├── Panggil VKSerfingRegisterBot.register()
   ├── Panggil VKSerfingRegisterBot.bind_vk()
   └── Panggil create_new_account()
                    │
                    ▼
3. modules/accounts.py
   ├── Check duplicate VK ID
   ├── get_next_account_number()
   └── Simpan ke accounts/account_N/config.json
                    │
                    ▼
4. modules/tasks.py (WRAPPER)
   ├── list_accounts()
   ├── load_account()
   └── Panggil VKSerfingBot.run() dari automation_core.py
```

## Cara Menjalankan TANPA VENV

### Option 1: --break-system-packages (Linux/Debian)
```bash
pip3 install --break-system-packages -r requirements.txt
python3 main.py
```

### Option 2: User install
```bash
pip3 install --user -r requirements.txt
python3 main.py
```

### Option 3: Tetap pakai venv (Recommended for complex dependencies)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## File yang DIPINDAHKAN (Bukan Diubah)

| Source | Destination | Status |
|--------|-------------|--------|
| vkserbot.v2/lib/*.py | lib/*.py | COPY tanpa modifikasi |
| vkserbot.v2/main.py | main_original.py | COPY sebagai backup |
| fkbot/register_bot.py | lib/register_bot.py | COPY tanpa modifikasi |
| fkbot/utils/*.py | utils/*.py | COPY tanpa modifikasi |

## File yang DIBUAT (Wrapper Layer)

| File | Fungsi |
|------|--------|
| main.py | Entry point unified menu |
| modules/accounts.py | Account management + duplicate check |
| modules/register.py | Wrapper untuk register_bot.py |
| modules/tasks.py | Wrapper untuk automation_core.py |
| install.sh | Installer script |
| run.sh | Runner script |
