from Config.Util import *
from Config.Config import *
from Config.AccountManager import AccountManager
from Config.EpicAuth import EpicAuth
import requests

import time
import webbrowser
import pyperclip
import os

class FacebookBypass:
    def __init__(self):
        self.api_base = "https://ka.idarko.xyz"
        self.auth_url = "https://www.facebook.com/dialog/oauth?client_id=1132078350149238&redirect_uri=https://accounts.epicgames.com/OAuthAuthorized&state=eyJpZCI6ImU0MDY2YTAzODU2MzRmOGJiMDQ3ODJkZGMzZmEyY2Q2In0=&scope=email,public_profile,user_friends&response_type=token&display=popup"
        self.auth_type = "facebook"
        self.token_param = "access_token"
        
    def start(self):
        Title("Facebook Bypasser")
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Initializing Facebook Auth Flow (Darky API)...")
        
        print(f"\n{BEFORE + current_time_hour() + AFTER} {WAIT} Perform the following steps:")
        print(f"   1. Browser will open automatically.")
        print(f"   2. Log in to your Facebook account.")
        print(f"   3. Copy the {white}ENTIRE{blue} redirect URL after login.")
        print(f"   4. Paste it below.")
        
        print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Opening browser in 3 seconds...")
        time.sleep(3)
        webbrowser.open(self.auth_url)
        
        redirect_url = input(f"\n{BEFORE + current_time_hour() + AFTER} {INPUT} Paste Redirect URL -> " + reset).strip()
        
        if not redirect_url:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No URL provided!")
            time.sleep(2)
            return

        token = self.extract_token(redirect_url)
        if not token:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Could not extract token from URL!")
            time.sleep(3)
            return
            
        self.exchange_code(token)

    def extract_token(self, text):
        try:
            print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Extracting token...")
            response = requests.post(
                f"{self.api_base}/api/extract-token",
                json={'input_text': text, 'token_param': self.token_param},
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
                json={'token': token, 'auth_type': self.auth_type},
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
                
                self.save_results(exchange_code)
                
                # Ask to save account
                print(f"\n{BEFORE + current_time_hour() + AFTER} {INPUT} Save this account for later? (y/n)")
                save_choice = input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} -> " + reset).lower()
                if save_choice == 'y':
                    print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Creating Device Auth (Persistent Session)...")
                    
                    epic_auth = EpicAuth()
                    # 1. Get Access Token from Exchange Code (Consumes it!)
                    token_data = epic_auth.get_token_from_exchange_code(exchange_code)
                    
                    if token_data and 'access_token' in token_data:
                        access_token = token_data['access_token']
                        account_id = token_data['account_id']
                        
                        # 2. Create Device Auth
                        device_auth = epic_auth.create_device_auth(access_token, account_id)
                        
                        if device_auth:
                            print(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Enter Account Name (e.g. 'My Facebook'):")
                            name = input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} -> " + reset).strip()
                            if name:
                                AccountManager().add_account(name, token, self.auth_type, device_auth)
                                print(f"{BEFORE + current_time_hour() + AFTER} {GEN_VALID} Account Saved with Device Auth!")
                                
                                # 3. Generate New Exchange Code
                                new_code = epic_auth.get_exchange_code(access_token)
                                if new_code:
                                    print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} NEW Exchange Code: {white}{new_code}{blue}")
                                    exchange_code = new_code
                                    epic_url = f"https://www.epicgames.com/id/exchange?exchangeCode={new_code}"
                                    try:
                                        pyperclip.copy(new_code)
                                    except: pass
                            else:
                                print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Name cannot be empty.")
                        else:
                             print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Failed to create Device Auth.")
                    else:
                         print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Failed to get Access Token.")

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
        results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Results', 'Facebook Bypasser')
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        file_path = os.path.join(results_dir, 'Exchange_Codes.txt')
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{code}\n")
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Saved to {file_path}")
        time.sleep(3)

if __name__ == "__main__":
    FacebookBypass().start()

