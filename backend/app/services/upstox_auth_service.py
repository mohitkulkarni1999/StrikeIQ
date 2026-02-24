import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import json
import os
import httpx
import urllib.parse
import hmac
import hashlib
import base64
import secrets
from ..core.config import settings

logger = logging.getLogger(__name__)

_auth_service_instance = None


class TokenExpiredError(Exception):
    pass


class UpstoxCredentials:
    def __init__(self, access_token: str, refresh_token: str, expires_in: int):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in or 3600)


class UpstoxAuthService:

    def __init__(self, credentials_file: str = "upstox_credentials.json"):
        self._credentials_file = credentials_file
        self._credentials = self._load_credentials()
        self._rate_limit_store = {}

    # ================= CLIENT IP =================
    def _get_client_ip(self, request):
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.client.host or '127.0.0.1'

    # ================= RATE LIMIT =================
    def _check_rate_limit(self, ip: str):
        now = datetime.now(timezone.utc)
        last = self._rate_limit_store.get(ip)

        if last and (now - last).seconds < 5:
            return False

        self._rate_limit_store[ip] = now
        return True

    # ================= STATE =================
    def generate_signed_state(self) -> str:
        ts = str(int(datetime.now(timezone.utc).timestamp()))
        rnd = secrets.token_urlsafe(16)
        payload = f"{ts}:{rnd}"

        secret = settings.SECRET_KEY.encode()
        sig = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()

        full = f"{payload}:{sig}"
        return base64.urlsafe_b64encode(full.encode()).decode()

    def validate_signed_state(self, state: str) -> bool:

        if not state:
            return False

        try:
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            ts, rnd, sig = decoded.split(":")

            payload = f"{ts}:{rnd}"
            secret = settings.SECRET_KEY.encode()
            expected = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()

            if not hmac.compare_digest(sig, expected):
                return False

            now = int(datetime.now(timezone.utc).timestamp())
            if now - int(ts) > 600:
                return False

            return True

        except:
            return False

    # ================= AUTH URL =================
    def get_authorization_url(self, state: str):

        encoded_redirect = urllib.parse.quote(settings.REDIRECT_URI, safe='')

        return (
            f"https://api.upstox.com/v2/login/authorization/dialog"
            f"?response_type=code"
            f"&client_id={settings.UPSTOX_API_KEY}"
            f"&redirect_uri={encoded_redirect}"
            f"&state={state}"
        )

    # ================= TOKEN =================
    def exchange_code_for_token(self, code: str):

        url = "https://api.upstox.com/v2/login/authorization/token"

        data = {
            "code": code,
            "client_id": settings.UPSTOX_API_KEY,
            "client_secret": settings.UPSTOX_API_SECRET,
            "redirect_uri": settings.REDIRECT_URI,
            "grant_type": "authorization_code"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = httpx.post(url, headers=headers, data=data)

        print("🔥 TOKEN RESPONSE:", response.text)

        if response.status_code != 200:
            raise Exception(response.text)

        token = response.json()

        creds = UpstoxCredentials(
            token.get("access_token"),
            token.get("refresh_token"),
            token.get("expires_in") or 3600
        )

        self._store_credentials(creds)
        return creds.access_token

    # ================= STORE =================
    def _store_credentials(self, creds: UpstoxCredentials):

        with open(self._credentials_file, "w") as f:
            json.dump({
                "access_token": creds.access_token,
                "refresh_token": creds.refresh_token,
                "expires_at": creds.expires_at.isoformat()
            }, f)

        self._credentials = creds

    def _load_credentials(self) -> Optional[UpstoxCredentials]:

        if not os.path.exists(self._credentials_file):
            return None

        try:
            with open(self._credentials_file, "r") as f:
                data = json.load(f)

            exp = datetime.fromisoformat(data["expires_at"])
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)

            if exp <= datetime.now(timezone.utc):
                return None

            c = UpstoxCredentials(data["access_token"], data.get("refresh_token"), 0)
            c.expires_at = exp
            return c

        except:
            return None

    async def get_valid_access_token(self):

        if not self._credentials:
            self._credentials = self._load_credentials()

        if self._credentials:
            return self._credentials.access_token

        raise TokenExpiredError("No valid credentials")

    def is_authenticated(self):

        if not self._credentials:
            self._credentials = self._load_credentials()

        return self._credentials is not None

    async def refresh_access_token(self):

        if not self._credentials or not self._credentials.refresh_token:
            raise TokenExpiredError("No refresh token available")

        url = "https://api.upstox.com/v2/login/authorization/token"

        data = {
            "refresh_token": self._credentials.refresh_token,
            "client_id": settings.UPSTOX_API_KEY,
            "client_secret": settings.UPSTOX_API_SECRET,
            "redirect_uri": settings.REDIRECT_URI,
            "grant_type": "refresh_token"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)

        if response.status_code != 200:
            raise TokenExpiredError(response.text)

        token_data = response.json()

        creds = UpstoxCredentials(
            token_data.get("access_token"),
            token_data.get("refresh_token"),
            token_data.get("expires_in") or 3600
        )

        self._store_credentials(creds)

        logger.info("Token refreshed successfully")

        return creds.access_token


def get_upstox_auth_service():
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = UpstoxAuthService()
    return _auth_service_instance