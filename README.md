# FKBot

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=800&size=35&pause=1000&color=00FF00&center=true&vCenter=true&random=false&width=435&lines=FKBOT+v2.0" alt="FKBOT" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/PLATFORM-VKSERFING-00ff00?style=for-the-badge" alt="Platform"/>
  <img src="https://img.shields.io/badge/VERSION-2.0-blue?style=for-the-badge" alt="Version"/>
  <img src="https://img.shields.io/badge/PYTHON-3.8+-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AUTO-REGISTER-red?style=flat-square" alt="Register"/>
  <img src="https://img.shields.io/badge/AUTO-TASK-red?style=flat-square" alt="Task"/>
  <img src="https://img.shields.io/badge/MULTI-ACCOUNT-red?style=flat-square" alt="Multi"/>
  <img src="https://img.shields.io/badge/PARALLEL-MODE-red?style=flat-square" alt="Parallel"/>
</p>

---

## ⚡ Quick Start

```bash
# 1. Clone repository
git clone https://github.com/ayamgorengkecap/fkbot.git
cd fkbot

# 2. Install dependencies
pip3 install --break-system-packages -r requirements.txt

# 3. Jalankan
python3 main.py
```

> **Note:** Flag `--break-system-packages` wajib untuk Ubuntu 23.04+ / Debian 12+. Kalau error, coba tanpa flag itu.

---

## 📋 Features

| Feature | Status |
|---------|--------|
| Auto Register | ✅ |
| Auto Task (VK, Telegram, Instagram) | ✅ |
| Multi Account | ✅ |
| Parallel Mode (10 accounts) | ✅ |
| Auto Captcha Solve (2Captcha) | ✅ |
| Withdraw to Volet | ✅ |
| Telegram Binding | ✅ |
| Instagram Binding | ✅ |

---

## 📱 Telegram API (Sudah Tersedia)

Script sudah include Telegram API credentials, **tidak perlu buat sendiri**:

| Key | Value |
|-----|-------|
| API ID | `1724399` |
| API Hash | `7f6c4af5220db320413ff672093ee102` |

Untuk bind Telegram ke akun:
1. Jalankan `python3 main.py`
2. Pilih menu **10. Bind Telegram**
3. Masukkan nomor HP Telegram
4. Input OTP yang dikirim ke Telegram

---

## 📂 Data Files (untuk Register Batch)

Kalau mau register banyak akun sekaligus, siapkan 3 file di folder `data/`:

### 1. data/emails.txt
Satu email per baris:
```
email1@gmail.com
email2@gmail.com
email3@gmail.com
```

### 2. data/vk_tokens.txt
VK OAuth URL lengkap, satu per baris. Cara dapat:
1. Buka link ini di browser: https://oauth.vk.com/authorize?client_id=2274003&scope=offline,wall,groups,friends,photos,status&response_type=token
2. Login VK
3. Copy URL hasil redirect (yang ada `access_token` dan `user_id`)

```
https://oauth.vk.com/blank.html#access_token=vk1.a.xxx&user_id=111111
https://oauth.vk.com/blank.html#access_token=vk1.a.yyy&user_id=222222
```

### 3. data/proxies.txt
Format: `IP:PORT:USERNAME:PASSWORD`
```
1.2.3.4:8080:user1:pass1
5.6.7.8:8080:user2:pass2
```

> **Penting:** Jumlah baris di ketiga file harus sama!

---

## 🎯 Menu Utama

```
    ███████╗██╗  ██╗██████╗  ██████╗ ████████╗
    ██╔════╝██║ ██╔╝██╔══██╗██╔═══██╗╚══██╔══╝
    █████╗  █████╔╝ ██████╔╝██║   ██║   ██║   
    ██╔══╝  ██╔═██╗ ██╔══██╗██║   ██║   ██║   
    ██║     ██║  ██╗██████╔╝╚██████╔╝   ██║   
    ╚═╝     ╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝   v2.0

▸ REGISTRASI
  1. Register batch (dari data/*.txt)
  2. Register manual (input satu-satu)

▸ JALANKAN TASK
  3. Run parallel (10 akun sekaligus)
  4. Run sequential (satu per satu)
  5. Run selected (pilih akun, loop otomatis)

▸ KELOLA AKUN
  6. List semua akun
  7. Cek akun duplicate
  8. Fetch balance semua akun

▸ BINDING
  9. Bind Instagram
  10. Bind Telegram

▸ WITHDRAW
  11. Withdraw ke Volet
```

---

## 💰 Cara Withdraw

1. Jalankan `python3 main.py`
2. Pilih menu **11. Withdraw ke Volet**
3. Pilih opsi **1. Withdraw to Volet**
4. Masukkan wallet Volet (format: `U XXXX XXXX XXXX`)
5. Konfirmasi, selesai!

Minimal withdraw: **103₽** (setelah fee 3%)

---

## 📞 Contact

<p align="center">
  <a href="https://t.me/aldo_tamvan">
    <img src="https://img.shields.io/badge/TELEGRAM-OWNER-blue?style=for-the-badge&logo=telegram" alt="Telegram"/>
  </a>
</p>

---

<p align="center">
  <img src="https://img.shields.io/badge/MADE%20WITH-❤️-red?style=for-the-badge" alt="Made with love"/>
</p>
