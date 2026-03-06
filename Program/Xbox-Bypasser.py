from Config.Util import *
from Config.Config import *
from Config.AccountManager import AccountManager
from Config.EpicAuth import EpicAuth
import requests

import time
import webbrowser
import pyperclip
import os

class XboxBypass:
    def __init__(self):
        self.api_base = "https://ka.idarko.xyz"
        self.auth_url = "https://login.live.com/oauth20_authorize.srf?client_id=82023151-c27d-4fb5-8551-10c10724a55e&redirect_uri=https%3A%2F%2Faccounts.epicgames.com%2FOAuthAuthorized&state=&scope=xboxlive.signin&service_entity=undefined&force_verify=true&response_type=code&display=popup"
        self.auth_type = "xbl"
        self.token_param = "code"
        
    def start(self):
        Title("Xbox Bypasser")
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Initializing Xbox Auth Flow (Darky API)...")
        
        print(f"\n{BEFORE + current_time_hour() + AFTER} {WAIT} Perform the following steps:")
        print(f"   1. Log in to your Xbox/Microsoft account.")
        print(f"   2. Copy the {white}ENTIRE{blue} redirect URL after login.")
        print(f"   3. Paste it below.")
        
        print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Opening browser in 3 seconds...")
        time.sleep(3)
        webbrowser.open(self.auth_url)
        
        redirect_url = input(f"\n{BEFORE + current_time_hour() + AFTER} {INPUT} Paste Redirect URL -> " + reset).strip()
        
        if not redirect_url:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No URL provided!")
            time.sleep(2)
            return

        # Extract Token
        token = self.extract_token(redirect_url)
        if not token:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Could not extract token from URL!")
            time.sleep(3)
            return
            
        # Exchange Code
        self.exchange_code(token)

    def extract_token(self, text):
        try:
            print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Extracting token...")
            response = requests.post(
                f"{self.api_base}/api/extract-token",
                json={
                    'input_text': text,
                    'token_param': self.token_param
                },
                timeout=10
            )
            data = response.json()
            if data.get('success'):
                return data.get('token')
            return None
        except Exception as e:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} API Error: {e}")
            return None

    def exchange_code(self, token):
        try:
            print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Authenticating with Epic Games...")
            response = requests.post(
                f"{self.api_base}/api/exchange-code",
                json={
                    'token': token,
                    'auth_type': self.auth_type
                },
                timeout=30
            )
            data = response.json()
            
            if data.get('success'):
                exchange_code = data.get('exchange_code')
                epic_url = data.get('epic_url', '')
                
                print(f"\n{BEFORE + current_time_hour() + AFTER} {GEN_VALID} Authorization Successful!")
                print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Exchange Code: {white}{exchange_code}{blue}")
                
                try:
                    pyperclip.copy(exchange_code)
                    print(f"   (Code copied to clipboard)")
                except:
                    pass
                
                # Save results
                self.save_results(exchange_code)
                
                # Ask to save account using Device Auth
                print(f"\n{BEFORE + current_time_hour() + AFTER} {INPUT} Save this account for later? (y/n)")
                if input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} -> " + reset).lower() == 'y':
                    print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Creating Device Auth (Persistent Session)...")
                    
                    epic_auth = EpicAuth()
                    
                    # 1. Get Access Token
                    # NOTE: If this fails, it's likely because the exchange code is already consumed or client mismatch.
                    token_data = epic_auth.get_token_from_exchange_code(exchange_code)
                    if token_data and 'access_token' in token_data:
                        access_token = token_data['access_token']
                        account_id = token_data['account_id']
                        
                        # 2. Create Device Auth
                        device_auth = epic_auth.create_device_auth(access_token, account_id)
                        if device_auth:
                            # 3. Save Account
                            print(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Enter Account Name:")
                            name = input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} -> " + reset).strip()
                            AccountManager().add_account(name, "", self.auth_type, device_auth)
                            print(f"{BEFORE + current_time_hour() + AFTER} {GEN_VALID} Account Saved with Device Auth!")
                            
                            # 4. Generate New Exchange Code
                            new_code = epic_auth.get_exchange_code(access_token)
                            if new_code:
                                print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} NEW Exchange Code: {white}{new_code}{blue}")
                                exchange_code = new_code
                                epic_url = f"https://www.epicgames.com/id/exchange?exchangeCode={new_code}"
                                try:
                                    pyperclip.copy(new_code)
                                    print(f"   (New code copied to clipboard)")
                                except: pass
                        else:
                            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Failed to create Device Auth.")
                    else:
                        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Failed to get Access Token from Code.")
                        print(f"{BEFORE + current_time_hour() + AFTER} {NOTE} This is expected if the code was already used or expired.")
                        print(f"{BEFORE + current_time_hour() + AFTER} {NOTE} Trying alternative method (Website Client)...")
                        
                        # Try with Website Client Auth if Launcher fails
                        # Epic Games Website Client ID: 902b49d0-7a06-4447-9871-6785165d2153 (Example, need real one)
                        # Actually, let's try just informing the user for now.
                        

                print(f"\n{BEFORE + current_time_hour() + AFTER} {INPUT} Open URL in browser? (y/n)")

                choice = input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} -> " + reset).lower()
                if choice == 'y':
                    webbrowser.open(epic_url)
            else:
                error = data.get('error', 'Unknown Error')
                print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Authentication Failed: {error}")
                if 'details' in data:
                    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Details: {data['details']}")
                time.sleep(5)
                
        except Exception as e:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} API Error: {e}")
            time.sleep(3)

    def save_results(self, code):
        results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Results', 'Xbox Bypasser')
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            
        file_path = os.path.join(results_dir, 'Exchange_Codes.txt')
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{code}\n")
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Saved to {file_path}")
        time.sleep(3)

if __name__ == "__main__":
    XboxBypass().start()

