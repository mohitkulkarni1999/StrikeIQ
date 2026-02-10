from typing import Optional
from datetime import datetime, timedelta
import json
import os
import httpx
from ..core.config import settings

class UpstoxCredentials:
    def __init__(self, access_token: str, refresh_token: str, expires_in: int):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = datetime.now() + timedelta(seconds=expires_in or 3600)

class UpstoxAuthService:
    def __init__(self, credentials_file: str = "upstox_credentials.json"):
        self._credentials_file = credentials_file
        self._credentials = self._load_credentials()

    def exchange_code_for_token(self, code: str) -> dict:
        try:
            url = "https://api.upstox.com/v2/login/authorization/token"
            headers = {
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "code": code,
                "client_id": settings.UPSTOX_API_KEY,
                "client_secret": settings.UPSTOX_API_SECRET,
                "redirect_uri": settings.REDIRECT_URI,
                "grant_type": "authorization_code"
            }
            
            with httpx.Client() as client:
                response = client.post(url, headers=headers, data=data)
                response.raise_for_status()
                token_data = response.json()
                
                credentials = UpstoxCredentials(
                    token_data.get("access_token"),
                    token_data.get("refresh_token"),
                    token_data.get("expires_in") or 3600
                )
                self._store_credentials(credentials)
                return {
                    "access_token": credentials.access_token,
                    "refresh_token": credentials.refresh_token,
                    "expires_at": credentials.expires_at.isoformat()
                }
        except Exception as e:
            raise Exception(f"Token exchange failed: {str(e)}")

    def _store_credentials(self, credentials: UpstoxCredentials):
        with open(self._credentials_file, 'w') as f:
            json.dump({
                "access_token": credentials.access_token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expires_at.isoformat()
            }, f)

    def _load_credentials(self) -> Optional[UpstoxCredentials]:
        if os.path.exists(self._credentials_file):
            with open(self._credentials_file, 'r') as f:
                data = json.load(f)
                expires_at = datetime.fromisoformat(data["expires_at"])
                # Recreate credentials with expires_at
                creds = UpstoxCredentials(data["access_token"], data["refresh_token"], 0)
                creds.expires_at = expires_at
                return creds
        return None

    def refresh_access_token(self):
        # Placeholder for refresh logic
        pass

    def get_valid_access_token(self) -> Optional[str]:
        if self._credentials and self._credentials.expires_at > datetime.now():
            return self._credentials.access_token
        elif self._credentials and self._credentials.refresh_token:
            self.refresh_access_token()
            return self._credentials.access_token if self._credentials else None
        return None

    def is_authenticated(self) -> bool:
        return self.get_valid_access_token() is not None

    def logout(self):
        if os.path.exists(self._credentials_file):
            os.remove(self._credentials_file)
        self._credentials = None
