import re
import json
import time
import random
import os
import threading
import uuid
import sys
import ctypes
import urllib.parse
import asyncio
from colorama import init, Fore, Style
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import Tk, filedialog
from datetime import datetime
from Config.Util import *
from curl_cffi import requests

# Load Flights
FLIGHTS_LIST = []
try:
    flights_path = os.path.join(os.getcwd(), 'Program', 'Config', 'flights.json')
    if os.path.exists(flights_path):
        with open(flights_path, 'r', encoding='utf-8') as f:
            FLIGHTS_LIST = json.load(f)
except Exception as e:
    pass

# Initialize Colorama
init(autoreset=True)

# Lock for thread-safe printing and file writing
print_lock = threading.RLock()
file_lock = threading.RLock()
pool_lock = threading.RLock()

# Configuration
try:
    config_path = os.path.join(os.getcwd(), 'Program', 'Config', 'config.json')
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        MAX_THREADS = int(config_data.get('threads', 50))
        USE_PROXY = config_data.get('proxies_enabled', True)
except Exception:
    MAX_THREADS = 50
    USE_PROXY = True

# Results Directory
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Results', 'Code Checker')
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

VALID_FILE = os.path.join(RESULTS_DIR, "Valid.txt")
INVALID_FILE = os.path.join(RESULTS_DIR, "Invalid.txt")
ERRORS_FILE = os.path.join(RESULTS_DIR, "Errors.txt")

# Stats
stats = {
    'valid': 0,
    'invalid': 0,
    'error': 0,
    'total': 0,
    'checked': 0
}

def update_title():
    Title(f"Xbox Code Checker | Checked: {stats['checked']}/{stats['total']} | Valid: {stats['valid']} | Invalid: {stats['invalid']} | Errors: {stats['error']} | Threads: {MAX_THREADS}")

def print_hit(code, product_name):
    with print_lock:
        print(f"{BEFORE + current_time_hour() + AFTER} {GEN_VALID} {white}{code}{reset} | {white}{product_name}{reset}")

def get_random_proxy(proxies):
    if not proxies:
        return None
    proxy = random.choice(proxies)
    if proxy.count("@") >= 1:
        credentials, addr = proxy.split("@", 1)
        username, password = credentials.split(":", 1)
        proxy_url = f"http://{username}:{password}@{addr}"
    elif proxy.count(':') == 3:
        ip, port, username, password = proxy.split(':')
        proxy_url = f"http://{username}:{password}@{ip}:{port}"
    else:
        proxy_url = f"http://{proxy}"
    
    return {
        'http': proxy_url,
        'https': proxy_url
    }

# ============================================================================
# AUTHENTICATOR (Reference Implementation)
# ============================================================================

def login_microsoft_account(email, password, proxies=None):
    session = requests.Session(impersonate="chrome")
    if proxies:
        session.proxies = proxies
    
    try:
        login_response = session.post(
            f"https://login.live.com/ppsecure/post.srf?username=%7bemail%7d&client_id=0000000048170EF2&contextid=072929F9A0DD49A4&opid=D34F9880C21AE341&bk=1765024327&uaid=a5b22c26bc704002ac309462e8d061bb&pid=15216&prompt=none",
            data = {'login': email, 'loginfmt': email, 'passwd': password, 'PPFT': "-Drzud3DzKKJtVD9IfM5xwJywwEjJp5zvvJmrSyu*RKOf!PbgSCQ7ReuKFS*sIpTV5r28epGtqBhqH3JYvND4!onwSWz2JEkvdeewUQC6HmAXRgjYBzSlf0mjEYbx3ULc7oy5fUK3LDSb*CnkAG03FLzwVPmT5WjYu4sE5Wqd93pCx0USJK4jelAWNvsMog0Rmj90tmeCd*1pDYjkINyPEgQSkv6y5GPuX!GmYwKccALUt*!SRaI02p*XUqePtNtJzw$$"},
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                "Cookie": "MSPRequ=id=N&lt=1765024327&co=1; uaid=a5b22c26bc704002ac309462e8d061bb; MSPOK=$uuid-90ce4cdb-2718-4d7e-9889-4136cfacc5b2; OParams=11O.DhmByHnT9kscyud7VyWQt5uWQuQOYWZ9O2v5E49mKxVoKsSZaB4KnwkAQCVjghW9A6M8syem4sO!g4KOfietehdD7U2eXeVo8eUsorIQv1deGf6v43egdNizv1*agwrVh2OTg7pu2SRE3SougNTvzlNUNe1BgtO4HFlLRm6UoEW3PNBIxuVPmFBiPs0wEU162jlfO8yA1!QZV7KKArG8NPChj0kf1IOfR95k0fIfa0!fDW8Md44pKHa3rkU0Um0KB03YEBdWMOAbJlX5RONIL3M31WhD4LG3GPAoBPAMCN9fMk2rHlwix8g6MOW3HKxDT4I0TlKrYHDBJejZWSmI23T3v2kr1MKaL9vEQoaTwOJf9VloMFBi7yB!kisHZn0BkjE!HGWhaliwYdluhJUCu1g$"
            },
            timeout=10,
            allow_redirects=False
        )
        
        if login_response.status_code != 302 or "error=interaction_required" in login_response.headers.get('Location', ''):
            with print_lock:
                 # Only print if it's not a common interaction error which happens often with bad accounts
                 if "error=interaction_required" not in login_response.headers.get('Location', ''):
                     print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Login Failed for {email} (Status: {login_response.status_code})")
            return None, None

        token = urllib.parse.unquote(login_response.headers['Location'].split('access_token=')[1].split('&')[0])

        # Pre-warm Store Session
        try:
            session.get(
                "https://buynowui.production.store-web.dynamics.com/akam/13/79883e11",
                timeout=10
            )
        except Exception as e:
            with print_lock:
                print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Pre-warm failed for {email}: {e}")
            
        return session, token
        
    except Exception as e:
        with print_lock:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Login Exception for {email}: {e}")
        return None, None

# ============================================================================
# STORE LOGIC
# ============================================================================

def get_store_cart_state(session, force_refresh=False, token=None):
    try:
        if force_refresh and hasattr(session, 'store_state'):
            delattr(session, 'store_state')
        if not force_refresh and hasattr(session, 'store_state'):
            return session.store_state
            
        ms_cv = "xddT7qMNbECeJpTq.6.2"
        url = 'https://www.microsoft.com/store/purchase/buynowui/redeemnow'
        params = {'ms-cv': ms_cv, 'market': 'US', 'locale': 'en-GB', 'clientName': 'AccountMicrosoftCom'}
        payload = {
            'data': '{"usePurchaseSdk":true}', 
            'market': 'US', 'cV': ms_cv, 'locale': 'en-GB', 
            'msaTicket': token, 'pageFormat': 'full', 
            'urlRef': 'https://account.microsoft.com/billing/redeem', 
            'isRedeem': 'true', 'clientType': 'AccountMicrosoftCom', 
            'scenario': 'redeem'
        }
        
        response = session.post(url, params=params, data=payload, timeout=30)
        match = re.search(r'window\.__STORE_CART_STATE__=({.*?});', response.text, re.DOTALL)
        if match:
            store_state = json.loads(match.group(1))
            extracted = {
                'ms_cv': store_state.get('appContext', {}).get('cv', ''),
                'correlation_id': store_state.get('appContext', {}).get('correlationId', ''),
                'tracking_id': store_state.get('appContext', {}).get('trackingId', ''),
                'vector_id': store_state.get('appContext', {}).get('vectorId', ''),
                'muid': store_state.get('appContext', {}).get('muid', ''),
                'alternative_muid': store_state.get('appContext', {}).get('alternativeMuid', '')
            }
            session.store_state = extracted
            return extracted
    except:
        pass
    return None

def generate_reference_id():
    timestamp_val = int(time.time() // 30)
    n = f'{timestamp_val:08X}'
    o = (uuid.uuid4().hex + uuid.uuid4().hex).upper()
    result = []
    for e in range(64):
        if e % 8 == 1:
            result.append(n[(e - 1) // 8])
        else:
            result.append(o[e])
    return "".join(result)

def prepare_redeem_api_call(session, code, headers, payload):
    try:
        response = session.post(
            'https://buynow.production.store-web.dynamics.com/v1.0/Redeem/PrepareRedeem/?appId=RedeemNow&context=LookupToken',
            headers=headers,
            json=payload,
            timeout=30
        )
        return response, None
    except Exception as e:
        return None, str(e)

def validate_code(session, code, token):
    try:
        store_state = get_store_cart_state(session, token=token)
        if not store_state:
            store_state = get_store_cart_state(session, force_refresh=True, token=token)
            if not store_state:
                return "ERROR", "Failed to get store state"

        headers = {
            "host": "buynow.production.store-web.dynamics.com",
            "connection": "keep-alive",
            "x-ms-tracking-id": store_state['tracking_id'],
            "sec-ch-ua-platform": "\"Windows\"",
            "authorization": f"WLID1.0=t={token}",
            "x-ms-client-type": "AccountMicrosoftCom",
            "x-ms-market": "US",
            "sec-ch-ua": "\"Chromium\";v=\"142\", \"Microsoft Edge\";v=\"142\", \"Not_A Brand\";v=\"99\"",
            "ms-cv": store_state['ms_cv'],
            "sec-ch-ua-mobile": "?0",
            "x-ms-reference-id": generate_reference_id(),
            "x-ms-vector-id": store_state['vector_id'],
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
            "x-ms-correlation-id": store_state['correlation_id'],
            "content-type": "application/json",
            "x-authorization-muid": store_state['alternative_muid'],
            "accept": "*/*",
            "origin": "https://www.microsoft.com",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://www.microsoft.com/",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9"
        }
        
        payload = {
            "market": "US", 
            "language": "en-US",
            "flights": FLIGHTS_LIST,
            "tokenIdentifierValue": code,
            "supportsCsvTypeTokenOnly": False,
            "buyNowScenario": "redeem",
            "clientContext": {"client": "AccountMicrosoftCom", "deviceFamily": "Web"}
        }

        # Direct synchronous call
        response, error = prepare_redeem_api_call(session, code, headers, payload)
        
        if error:
            return "ERROR", f"Request Error: {error}"
            
        if response is None:
            return "ERROR", "Request failed (No Response object)"
            
        # Debug non-200 responses
        if response.status_code != 200:
             # with print_lock:
             #     print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} API Status {response.status_code}: {response.text[:100]}")
             pass

        if response.status_code == 429:
            return "RATE_LIMITED", "429"
            
        try:
            data = response.json()
        except:
            # If JSON fails, it might be a WAF block or HTML error page
            if "Access Denied" in response.text or "unauthorized" in response.text.lower():
                return "ERROR", f"Access Denied (WAF/Block) - Status: {response.status_code}"
            return "ERROR", f"Invalid JSON (Status {response.status_code}): {response.text[:100]}"
        
        if "tokenType" in data and data["tokenType"] == "CSV":
            return "VALID", f"{data.get('value')} {data.get('currency')}"
            
        if "products" in data and len(data["products"]) > 0:
            product = data["products"][0]
            title = product.get("sku", {}).get("title", "Unknown")
            return "VALID", title
            
        if "events" in data and "cart" in data["events"]:
            for event in data["events"]["cart"]:
                if "data" in event and "reason" in event["data"]:
                    return "INVALID", event["data"]["reason"]
        
        # Check specific error codes from check.py
        if "errorCode" in data and data["errorCode"] == "TooManyRequests":
            return "RATE_LIMITED", "TooManyRequests"
            
        return "INVALID", "Unknown response"

    except Exception as e:
        return "ERROR", str(e)

def worker(account_pool, code_pool, proxies):
    worker_id = threading.current_thread().ident
    with print_lock:
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Worker {worker_id} started")
    
    while True:
        try:
            # Get an account
            account = None
            with pool_lock:
                if account_pool:
                    account = random.choice(account_pool)
            
            if not account:
                # No more accounts available, but we should still try to process remaining codes
                # Wait a bit and try again, or exit if no codes left
                time.sleep(1)
                with pool_lock:
                    if not code_pool:  # No more codes to process
                        with print_lock:
                            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Worker {worker_id} exiting - no more codes")
                        return
                continue
                
            email, password = account
            proxy = get_random_proxy(proxies) if USE_PROXY else None
            
            with print_lock:
                print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Worker {worker_id} attempting login for {email}")
            
            # Authenticate
            session, token = login_microsoft_account(email, password, proxy)
            
            if not token:
                with print_lock:
                    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Worker {worker_id} failed to authenticate {email}")
                continue
                
            with print_lock:
                 print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Worker {worker_id} logged in as {email} - Checking codes...")
            
            # Process codes with this account until rate limited or no more codes
            consecutive_errors = 0
            
            while True:
                code = None
                with pool_lock:
                    if code_pool:
                        code = code_pool.pop(0)
                        with print_lock:
                            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Worker {worker_id} got code: {code[:10]}...")
                
                if not code:
                    with print_lock:
                        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Worker {worker_id} - no more codes to check")
                    return # No more codes to check
                
                # Clean Code (Handle URLs)
                original_code = code
                if 'code=' in code:
                    try:
                        code = code.split('code=')[1].split('&')[0].strip()
                        with print_lock:
                            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Worker {worker_id} extracted code: {code}")
                    except:
                        pass
                code = code.split('|')[0].strip().replace(':', '') # Extra cleanup
                
                with print_lock:
                    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Worker {worker_id} validating code: {code}")
                
                status, msg = validate_code(session, code, token)
                
                with file_lock:
                    stats['checked'] += 1
                    
                if status == "VALID":
                    print_hit(code, msg)
                    with file_lock:
                        stats['valid'] += 1
                        with open(VALID_FILE, 'a') as f:
                            f.write(f"{code} | {msg}\n")
                    consecutive_errors = 0
                    with print_lock:
                        print(f"{BEFORE + current_time_hour() + AFTER} {GEN_VALID} Worker {worker_id} found VALID code: {code}")
                            
                elif status == "RATE_LIMITED":
                    # Put code back and switch to a different account
                    with pool_lock:
                        code_pool.append(code)
                    with print_lock:
                        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Worker {worker_id} rate limited, switching account")
                    break # Switch account
                    
                elif status == "ERROR":
                    with print_lock:
                        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Worker {worker_id} code error {code}: {msg}")
                    with file_lock:
                        stats['error'] += 1
                        with open(ERRORS_FILE, 'a') as f:
                            f.write(f"{code} | {msg}\n")
                    consecutive_errors += 1
                    
                else: # INVALID, REDEEMED, ETC
                    with file_lock:
                        stats['invalid'] += 1
                        with open(INVALID_FILE, 'a') as f:
                            f.write(f"{code} | {msg}\n")
                    consecutive_errors = 0
                    with print_lock:
                        print(f"{BEFORE + current_time_hour() + AFTER} {GEN_INVALID} Worker {worker_id} found INVALID code: {code}")
                
                update_title()
                
                if consecutive_errors > 5:
                    with print_lock:
                        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Worker {worker_id} too many errors, switching account")
                    break

        except Exception as e:
            with print_lock:
                 print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Worker {worker_id} error: {e}")
            time.sleep(1)

def main():
    Title("Xbox Code Checker")
    Clear()
    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Xbox Code Checker")
    
    acc_path = None
    code_path = None
    
    # Check for auto mode
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        if len(sys.argv) >= 4:
            code_path = sys.argv[3]  # Only use the codes file from auto mode
            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Auto-loading codes from Code Puller...")
            time.sleep(1)
            
    # 1. Load Accounts (Always show dialog, even in auto mode)
    print(f"\n{BEFORE + current_time_hour() + AFTER} {WAIT} Select Accounts File...")
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    acc_path = filedialog.askopenfilename(title="Select Accounts File", filetypes=[("Text Files", "*.txt")])
    root.destroy()
    
    if not acc_path:
        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No accounts file selected. Exiting.")
        return

    accounts = []
    with open(acc_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if ':' in line:
                parts = line.strip().split(':', 1)
                accounts.append((parts[0].strip(), parts[1].strip()))
    
    # 2. Load Codes
    if not code_path:
        print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Select Codes File...")
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        code_path = filedialog.askopenfilename(title="Select Codes File", filetypes=[("Text Files", "*.txt")])
        root.destroy()
    
    if not code_path:
        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No codes file selected. Exiting.")
        return

    codes = []
    with open(code_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            c = line.strip().split('|')[0].strip()
            if len(c) > 10:
                codes.append(c)

    stats['total'] = len(codes)
    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Loaded {len(accounts)} accounts and {len(codes)} codes")

    # 3. Load Proxies
    proxies = []
    if USE_PROXY:
        try:
            if os.path.exists('proxies.txt'):
                with open('proxies.txt', 'r') as f:
                    proxies = [l.strip() for l in f if l.strip()]
        except:
            pass

    # 4. Start Threads
    print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Starting threads...")
    
    active_workers = min(MAX_THREADS, len(accounts), len(codes))
    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Starting {active_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=active_workers) as executor:
        futures = []
        for i in range(active_workers):
            future = executor.submit(worker, accounts, codes, proxies)
            futures.append(future)
        
        # Wait for all workers to complete with timeout
        for future in as_completed(futures, timeout=300):  # 5 minute timeout
            try:
                future.result()
            except Exception as e:
                print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Worker completed with error: {e}")
            
    print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Finished!")
    input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Press Enter to exit...")

if __name__ == "__main__":
    main()
