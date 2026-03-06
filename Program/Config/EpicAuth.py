import requests
import base64

class EpicAuth:
    def __init__(self):
        self.user_agent = "EpicGamesLauncher/11.0.1-14497462+++Portal+Release-Live-Windows (Windows/10.0.19041.1.768.64bit)"
        self.launcher_auth = "MzRhMDJjZjhmNDQxNGUyOWIxNTkyMTg3NmRhMzZmOWE6ZGFhZmJjY2M3Mzc3NDUwMzlkZmZlNTNkOTRmYzljNzk="
        self.common_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": self.user_agent
        }

    def get_token_from_exchange_code(self, exchange_code):
        """Exchanges an exchange code for an access token using Launcher Client"""
        url = "https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token"
        headers = self.common_headers.copy()
        headers["Authorization"] = f"Basic {self.launcher_auth}"
        
        data = {
            "grant_type": "exchange_code",
            "exchange_code": exchange_code
        }
        
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
            
        # Debugging
        print(f"[EpicAuth] Error getting token: {response.status_code} - {response.text}")
        return None

    def create_device_auth(self, access_token, account_id):
        """Creates a device auth for the account"""
        url = f"https://account-public-service-prod.ol.epicgames.com/account/api/public/account/{account_id}/deviceAuth"
        headers = self.common_headers.copy()
        headers["Authorization"] = f"Bearer {access_token}"
        
        response = requests.post(url, headers=headers, json={})
        if response.status_code == 200:
            return response.json()
        return None

    def get_token_from_device_auth(self, account_id, device_id, device_secret):
        """Gets an access token using device auth"""
        url = "https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token"
        headers = self.common_headers.copy()
        headers["Authorization"] = f"Basic {self.launcher_auth}"
        
        data = {
            "grant_type": "device_auth",
            "account_id": account_id,
            "device_id": device_id,
            "secret": device_secret
        }
        
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        return None

    def get_exchange_code(self, access_token):
        """Generates a new exchange code from an access token"""
        url = "https://account-public-service-prod.ol.epicgames.com/account/api/oauth/exchange"
        headers = self.common_headers.copy()
        headers["Authorization"] = f"Bearer {access_token}"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("code")
        return None
