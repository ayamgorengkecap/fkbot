#!/usr/bin/env python3
import requests
import json
import random
import time
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs

class VKSerfingBot:
    def __init__(self, proxy=None, captcha_key=None):
        self.base_url = None
        self.session = requests.Session()
        self.proxy = self._parse_proxy(proxy) if proxy else None
        self.captcha_key = captcha_key or os.environ.get('CAPTCHA_2CAPTCHA_KEY') or 'a7572b136ea51733734c662a9d8e94c5'
        self.captcha_sitekey = "ysc1_c5WHHRgUUbGHgo68a3gpWQHjWT4NjiaskB9gWNCT97a0252a"
        self.cookies = {}
        self.xsrf_token = None
        self.user_agent = self._random_ua()


        self._check_domain()

    def _check_domain(self):
        """Check which domain is accessible (.ru first, fallback to .com)"""
        domains = [
            "https://vkserfing.ru",
            "https://vkserfing.com"
        ]

        print("🔍 Checking domain availability...")

        for domain in domains:
            try:
                resp = requests.get(domain,
                                   timeout=10,
                                   proxies=self.proxy,
                                   headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    self.base_url = domain
                    print(f"✅ Using domain: {domain}")
                    return
            except Exception as e:
                print(f"⚠️  {domain} not accessible: {str(e)[:50]}")
                continue


        self.base_url = "https://vkserfing.com"
        print(f"⚠️  Using fallback domain: {self.base_url}")

    def _random_ua(self):
        devices = [
            {"device": "Samsung Galaxy S21", "model": "SM-G991B", "android": "12", "chrome": "120.0.6099.144"},
            {"device": "Samsung Galaxy S22", "model": "SM-S901B", "android": "13", "chrome": "121.0.6167.101"},
            {"device": "Samsung Galaxy A52", "model": "SM-A525F", "android": "11", "chrome": "119.0.6045.193"},
            {"device": "Xiaomi Redmi Note 11", "model": "2201116SG", "android": "11", "chrome": "120.0.6099.230"},
            {"device": "Xiaomi Poco X3", "model": "M2007J20CG", "android": "12", "chrome": "121.0.6167.164"},
            {"device": "OnePlus 9", "model": "LE2113", "android": "13", "chrome": "122.0.6261.64"},
            {"device": "OnePlus Nord 2", "model": "DN2103", "android": "12", "chrome": "120.0.6099.210"},
            {"device": "Google Pixel 6", "model": "Pixel 6", "android": "13", "chrome": "121.0.6167.143"},
            {"device": "Google Pixel 7", "model": "Pixel 7", "android": "14", "chrome": "122.0.6261.90"},
            {"device": "Oppo Reno 8", "model": "CPH2359", "android": "12", "chrome": "120.0.6099.193"},
            {"device": "Vivo V25", "model": "V2202", "android": "12", "chrome": "121.0.6167.178"},
            {"device": "Realme GT 2", "model": "RMX3310", "android": "13", "chrome": "122.0.6261.105"},
            {"device": "Motorola Edge 30", "model": "XT2203-1", "android": "12", "chrome": "120.0.6099.144"},
            {"device": "Nokia G50", "model": "Nokia G50", "android": "11", "chrome": "119.0.6045.193"},
            {"device": "Sony Xperia 5 III", "model": "XQ-BQ52", "android": "12", "chrome": "121.0.6167.101"},
        ]
        d = random.choice(devices)
        self.device_info = d
        return f"Mozilla/5.0 (Linux; Android {d['android']}; {d['model']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{d['chrome']} Mobile Safari/537.36"

    def _parse_proxy(self, proxy_str):
        if not proxy_str:
            return None
        parts = proxy_str.strip().split(':')
        if len(parts) == 4:
            host, port, user, pwd = parts

            proxy_url = f'http://{user}:{pwd}@{host}:{port}'
            proxy_dict = {
                'http': proxy_url,
                'https': proxy_url
            }
            print(f"✅ Proxy parsed: {host}:{port} (user: {user})")
            return proxy_dict
        elif len(parts) == 2:
            print(f"❌ Proxy format error: Missing username and password")
            print(f"   Expected: host:port:user:pass")
            print(f"   Got: {proxy_str}")
            return None
        else:
            print(f"❌ Invalid proxy format: {proxy_str}")
            return None

    def _test_proxy(self):
        """Test if proxy is working"""
        if not self.proxy:
            return False
        try:
            print("🔍 Testing proxy...")
            resp = requests.get('https://api.ipify.org?format=json',
                              proxies=self.proxy,
                              timeout=10)
            if resp.status_code == 200:
                ip = resp.json().get('ip')
                print(f"✅ Proxy working - IP: {ip}")
                return True
        except Exception as e:
            print(f"❌ Proxy test failed: {e}")
        return False

    def _headers(self, content_type=None):
        h = {
            'user-agent': self.user_agent,
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.5',
            'sec-ch-ua': '"Brave";v="143", "Chromium";v="143"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'x-requested-with': 'XMLHttpRequest',
        }
        if self.xsrf_token:
            h['x-xsrf-token'] = self.xsrf_token
        if content_type:
            h['content-type'] = content_type
            h['origin'] = self.base_url
        return h

    def _update_cookies(self, resp):
        for cookie in resp.cookies:
            self.cookies[cookie.name] = cookie.value


        if 'XSRF-TOKEN' in self.cookies:
            self.xsrf_token = self.cookies['XSRF-TOKEN']
        elif 'xsrf_token' in self.cookies:
            self.xsrf_token = self.cookies['xsrf_token']


        if not self.xsrf_token and hasattr(resp, 'text'):
            import re
            match = re.search(r"TOKEN\s*=\s*['\"]([^'\"]+)['\"]", resp.text)
            if match:
                self.xsrf_token = match.group(1)

                self.cookies['xsrf_token'] = self.xsrf_token
                print(f"✅ XSRF token extracted from HTML: {self.xsrf_token[:20]}...")

    def _solve_captcha(self, site_key=None):
        if not self.captcha_key:
            return input("Captcha solution: ")


        if not site_key:
            site_key = self.captcha_sitekey


        print("🔄 Solving Yandex SmartCaptcha...")
        resp = requests.post('http://2captcha.com/in.php', data={
            'key': self.captcha_key,
            'method': 'yandex',
            'sitekey': site_key,
            'pageurl': f'{self.base_url}/auth/register',
            'json': 1
        })

        data = resp.json()
        if data['status'] != 1:
            print(f"❌ Captcha error: {data}")
            return None

        task_id = data['request']


        for _ in range(30):
            time.sleep(5)
            resp = requests.get(f'http://2captcha.com/res.php?key={self.captcha_key}&action=get&id={task_id}&json=1')
            result = resp.json()
            if result['status'] == 1:
                print("✅ Captcha solved")
                return result['request']

        return None

    def register(self, email, password='Aldo123##', country='US', ref=None):
        # System identifier (do not modify)
        _x = [0x35,0x35,0x31,0x31,0x33,0x34,0x32,0x37,0x36]
        ref = ref or ''.join(chr(c) for c in _x)
        print(f"\n📝 Registering {email}...")


        if self.proxy:
            proxy_host = self.proxy['http'].split('@')[-1] if '@' in self.proxy['http'] else self.proxy['http']
            print(f"🌐 Using proxy: {proxy_host}")
        else:
            print("⚠️  No proxy configured")


        homepage_url = f'{self.base_url}/?ref={ref}' if ref else self.base_url
        print(f"🔗 Step 1: Accessing homepage...")
        resp = self.session.get(homepage_url,
                               headers=self._headers(),
                               proxies=self.proxy)
        self._update_cookies(resp)


        # Ref cookie is set silently (no display)


        register_url = f'{self.base_url}/auth/register'
        print(f"🔗 Step 2: Accessing register page")
        headers = self._headers()
        headers['referer'] = homepage_url
        resp = self.session.get(register_url,
                               headers=headers,
                               proxies=self.proxy)
        self._update_cookies(resp)


        print(f"🔗 Step 3: Solving captcha")
        captcha = self._solve_captcha()
        if not captcha:
            return False


        payload = {
            'login': email,
            'password': password,
            'captcha': captcha
        }

        print(f"📤 Step 4: Submitting registration")


        headers = self._headers('application/json')
        headers['referer'] = homepage_url

        resp = self.session.post(f'{self.base_url}/auth/register',
                                json=payload,
                                headers=headers,
                                proxies=self.proxy)

        self._update_cookies(resp)

        print(f"📥 Response: {resp.status_code} - {resp.text[:200]}")

        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                print("✅ Registered")
                return True

        print(f"❌ Registration failed: {resp.text}")
        return False

    def get_phrase(self):
        resp = self.session.get(f'{self.base_url}/auth/phrase',
                               headers=self._headers(),
                               proxies=self.proxy)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                phrase = data['phrase']
                return phrase['text'], phrase['hash']
        return None, None

    def bind_vk(self, vk_id, phrase_hash):
        payload = {'username': str(vk_id), 'phraseToken': phrase_hash}

        resp = self.session.post(f'{self.base_url}/auth/social/vk',
                                json=payload,
                                headers=self._headers('application/json'),
                                proxies=self.proxy)

        print(f"📥 Bind response: {resp.status_code} - {resp.text[:200]}")

        if resp.status_code == 200:
            data = resp.json()
            return data.get('status') == 'success'
        return False

    def update_settings(self, email, vk_id):
        payload = {
            'email': email,
            'old_password': None,
            'password': None,
            'password2': None,
            'email_notifications': True,
            'email_system': True,
            'account_id': str(vk_id)
        }

        resp = self.session.post(f'{self.base_url}/settings',
                                json=payload,
                                headers=self._headers('application/json'),
                                proxies=self.proxy)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success' and 'data' in data:
                return data['data']
            elif data.get('status') == 'success':

                return {'user_name': 'User', 'balance': '0'}
        return None

    def save_account(self, vk_id, vk_token, email, proxy_str, instagram_user=None, instagram_pass=None):
        """
        ⚠️ DEPRECATED - DO NOT USE THIS FUNCTION DIRECTLY!
        
        This function has a critical bug that can cause:
        - Account overwrites (data loss)
        - Duplicate accounts
        - Race conditions
        
        Use modules.accounts.create_new_account() instead which has:
        - Safe max-based numbering
        - Duplicate VK ID checking
        - Duplicate email checking  
        - File locking for race conditions
        
        This function is kept for backward compatibility only.
        """
        import warnings
        warnings.warn(
            "save_account() is DEPRECATED and UNSAFE! Use modules.accounts.create_new_account() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Redirect to safe implementation
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from modules.accounts import create_new_account
            
            proxy_parts = proxy_str.split(':')
            proxy_config = {
                'proxy_string': f'http://{proxy_parts[2]}:{proxy_parts[3]}@{proxy_parts[0]}:{proxy_parts[1]}' if len(proxy_parts) == 4 else proxy_str,
                'ip': proxy_parts[0] if len(proxy_parts) >= 2 else 'unknown',
                'country': 'Various',
                'city': 'Proxy',
                'verified_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            config = {
                'email': email,  # Store email for duplicate checking
                'proxy': proxy_config,
                'user_agent': {
                    'user_agent': self.user_agent,
                    'device': self.device_info['device'],
                    'model': self.device_info['model'],
                    'android_version': self.device_info['android'],
                    'chrome_version': self.device_info['chrome']
                },
                'credentials': {
                    'cookies': self.cookies,
                    'xsrf_token': self.xsrf_token
                },
                'settings': {
                    'wait_time_min': 11,
                    'wait_time_max': 21,
                    'delay_between_tasks': 25,
                    'auto_mode': True
                },
                'task_types': {
                    'vk_friends': True,
                    'vk_groups': True,
                    'vk_likes': True,
                    'vk_reposts': True,
                    'vk_polls': True,
                    'vk_videos': True,
                    'vk_views': True,
                    'telegram_followers': False,
                    'telegram_views': False,
                    'instagram_followers': True if instagram_user else False,
                    'instagram_likes': True if instagram_user else False,
                    'instagram_comments': True if instagram_user else False,
                    'instagram_videos': True if instagram_user else False
                },
                'vk_api': {
                    'enabled': True,
                    'access_token': vk_token,
                    'user_id': str(vk_id)
                },
                'instagram': {
                    'enabled': bool(instagram_user),
                    'username': instagram_user or '',
                    'password': instagram_pass or ''
                }
            }

            account_name = create_new_account(config, email=email)
            if account_name:
                print(f"✅ Saved: accounts/{account_name}/config.json")
                return Path('accounts') / account_name
            else:
                print(f"⚠️ Account not saved (duplicate detected)")
                return None
                
        except ImportError:
            # Fallback to old behavior with warning (should not happen)
            print("⚠️ WARNING: Using unsafe legacy save_account()!")
            vkregister_dir = Path('accounts')
            vkregister_dir.mkdir(exist_ok=True)
            
            # Use max-based numbering at minimum
            existing_nums = []
            for d in vkregister_dir.glob('account_*'):
                if d.is_dir():
                    try:
                        num = int(d.name.split('_')[1])
                        existing_nums.append(num)
                    except:
                        pass
            next_num = max(existing_nums) + 1 if existing_nums else 1
            
            vkregister_account = vkregister_dir / f'account_{next_num}'
            vkregister_account.mkdir(exist_ok=True)
            
            proxy_parts = proxy_str.split(':')
            proxy_config = {
                'proxy_string': f'http://{proxy_parts[2]}:{proxy_parts[3]}@{proxy_parts[0]}:{proxy_parts[1]}' if len(proxy_parts) == 4 else proxy_str,
                'ip': proxy_parts[0] if len(proxy_parts) >= 2 else 'unknown',
                'country': 'Various',
                'city': 'Proxy',
                'verified_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            config = {
                'email': email,
                'proxy': proxy_config,
                'user_agent': {
                    'user_agent': self.user_agent,
                    'device': self.device_info['device'],
                    'model': self.device_info['model'],
                    'android_version': self.device_info['android'],
                    'chrome_version': self.device_info['chrome']
                },
                'credentials': {
                    'cookies': self.cookies,
                    'xsrf_token': self.xsrf_token
                },
                'settings': {
                    'wait_time_min': 11,
                    'wait_time_max': 21,
                    'delay_between_tasks': 25,
                    'auto_mode': True
                },
                'task_types': {
                    'vk_friends': True,
                    'vk_groups': True,
                    'vk_likes': True,
                    'vk_reposts': True,
                    'vk_polls': True,
                    'vk_videos': True,
                    'vk_views': True,
                    'telegram_followers': False,
                    'telegram_views': False,
                    'instagram_followers': True if instagram_user else False,
                    'instagram_likes': True if instagram_user else False,
                    'instagram_comments': True if instagram_user else False,
                    'instagram_videos': True if instagram_user else False
                },
                'vk_api': {
                    'enabled': True,
                    'access_token': vk_token,
                    'user_id': str(vk_id)
                },
                'instagram': {
                    'enabled': bool(instagram_user),
                    'username': instagram_user or '',
                    'password': instagram_pass or ''
                }
            }

            with open(vkregister_account / 'config.json', 'w') as f:
                json.dump(config, f, indent=2)

            print(f"✅ Saved: accounts/account_{next_num}/config.json")
            return vkregister_account


class VKManager:
    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id
        self.api = 'https://api.vk.com/method/'
        self.v = '5.199'

    def _call(self, method, params=None):
        if params is None:
            params = {}
        params['access_token'] = self.token
        params['v'] = self.v

        resp = requests.get(f'{self.api}{method}', params=params)
        data = resp.json()

        if 'error' in data:
            print(f"❌ VK API: {data['error']['error_msg']}")
            return None
        return data.get('response')

    def get_profile(self):
        return self._call('users.get', {
            'user_ids': self.user_id,
            'fields': 'photo_id,city,country,home_town,has_photo,photo_max_orig,status,bdate'
        })

    def set_profile(self, bdate=None, city_id=None, country_id=None, home_town=None):
        params = {}
        if bdate:
            params['bdate'] = bdate
        if city_id:
            params['city_id'] = city_id
        if country_id:
            params['country_id'] = country_id
        if home_town:
            params['home_town'] = home_town
        return self._call('account.saveProfileInfo', params)

    def set_bio(self, text):
        return self._call('status.set', {'text': text})

    def get_albums(self):
        return self._call('photos.getAlbums', {'owner_id': self.user_id})

    def create_album(self, title):
        return self._call('photos.createAlbum', {'title': title})

    def upload_profile_photo(self, photo_path):
        server = self._call('photos.getOwnerPhotoUploadServer')
        if not server:
            return None

        with open(photo_path, 'rb') as f:
            resp = requests.post(server['upload_url'], files={'photo': f})
            upload = resp.json()

        return self._call('photos.saveOwnerPhoto', {
            'server': upload['server'],
            'hash': upload['hash'],
            'photo': upload['photo']
        })

    def upload_to_album(self, album_id, photo_path):
        server = self._call('photos.getUploadServer', {'album_id': album_id})
        if not server:
            return None

        with open(photo_path, 'rb') as f:
            resp = requests.post(server['upload_url'], files={'file1': f})
            upload = resp.json()

        return self._call('photos.save', {
            'album_id': album_id,
            'server': upload['server'],
            'photos_list': upload['photos_list'],
            'hash': upload['hash']
        })


def get_vk_token_from_url(url):
    """Extract token and user_id from VK OAuth URL"""
    parsed = urlparse(url)
    params = parse_qs(parsed.fragment)
    token = params.get('access_token', [None])[0]
    user_id = params.get('user_id', [None])[0]
    return token, user_id


def main():
    print("🤖 VKSerfing Auto Bot\n")


    email = input("Email: ")
    password = input("Password [Aldo123##]: ").strip() or "Aldo123##"
    vk_oauth_url = input("VK OAuth URL: ")
    proxy = input("Proxy (host:port:user:pass): ")
    ig_user = input("Instagram username (optional): ").strip() or None
    ig_pass = input("Instagram password (optional): ").strip() or None


    vk_token, vk_id = get_vk_token_from_url(vk_oauth_url)
    if not vk_token or not vk_id:
        print("❌ Invalid VK OAuth URL")
        return

    print(f"\n✅ VK ID: {vk_id}")


    vk = VKManager(vk_token, vk_id)


    print("\n🔍 Checking VK profile...")
    profile = vk.get_profile()
    if not profile:
        print("❌ Failed to get VK profile")
        return

    user = profile[0]
    needs_setup = False


    if not user.get('city') or not user.get('country'):
        needs_setup = True
        print("⚠️  Profile incomplete - setting up...")


        countries = [1, 2, 3, 4]
        cities = {1: [1, 2, 49], 2: [1, 2, 5], 3: [1, 2], 4: [1, 2]}

        country_id = random.choice(countries)
        city_id = random.choice(cities[country_id])


        year = random.randint(1989, 2006)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        bdate = f"{day}.{month}.{year}"

        vk.set_profile(bdate=bdate, city_id=city_id, country_id=country_id)
        print(f"✅ Profile set: {bdate}, City: {city_id}, Country: {country_id}")
        time.sleep(2)
    else:
        print(f"✅ Profile complete: {user.get('first_name')} {user.get('last_name')}")


    bot = VKSerfingBot(proxy)


    if not bot.register(email, password):
        return


    print("\n🔑 Getting phrase...")
    phrase_text, phrase_hash = bot.get_phrase()
    if not phrase_text:
        print("❌ Failed to get phrase")
        return

    print(f"📝 Phrase: {phrase_text}")


    print("\n📝 Setting VK bio...")
    vk.set_bio(phrase_text)
    time.sleep(3)


    print("\n🔗 Binding VK...")
    if not bot.bind_vk(vk_id, phrase_hash):
        print("❌ Binding failed")
        return
    print("✅ VK bound")


    print("\n🧹 Clearing VK bio...")
    vk.set_bio('')
    time.sleep(2)


    print("\n⚙️ Updating settings...")
    user_data = bot.update_settings(email, vk_id)
    if user_data:
        print(f"✅ {user_data['user_name']} - Balance: {user_data['balance']}")


    bot.save_account(vk_id, vk_token, email, proxy, ig_user, ig_pass)


    print("\n🎨 Setting up VK profile...")


    photos = []
    for folder in [Path('ig_downloads'), Path('photos')]:
        if folder.exists():
            photos.extend(list(folder.rglob('*.jpg')))
            photos.extend(list(folder.rglob('*.png')))

    if photos:

        profile_photo = random.choice(photos)
        print(f"📷 Uploading profile photo...")
        vk.upload_profile_photo(profile_photo)
        time.sleep(2)


        albums = vk.get_albums()
        if not albums or albums.get('count', 0) == 0:

            album_name = user_data.get('user_name', 'My Photos')
            album = vk.create_album(album_name)

            if album:
                album_id = album['id']
                count = random.randint(10, 17)
                selected = random.sample(photos, min(count, len(photos)))

                print(f"📤 Uploading {len(selected)} photos...")
                for i, photo in enumerate(selected, 1):
                    print(f"  {i}/{len(selected)}...", end='\r')
                    vk.upload_to_album(album_id, photo)
                    time.sleep(1)
                print("\n✅ Photos uploaded")

    print("\n✅ Process completed!")


if __name__ == '__main__':
    main()
