import hmac
import hashlib

from django.conf import settings

import requests


class RazorpayClient:
    def __init__(self, key=None, secret=None, account_number=None, base_url="https://api.razorpay.com/v1", timeout=20, session=None):
        self.key = key or getattr(settings, "RAZORPAY_KEY", "")
        self.secret = secret or getattr(settings, "RAZORPAY_SECRET_KEY", "")
        self.account_number = account_number or getattr(settings, "ACCOUNT_NUMBER", "")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def _auth(self):
        if not self.key or not self.secret:
            raise ValueError("Razorpay Credentials Are Not Configured.")
        return (self.key, self.secret)

    def create_order(self, amount, currency="INR", receipt="", notes=None):
        payload = {"amount": int(amount), "currency": currency, "receipt": receipt, "notes": notes or {}}
        response = self.session.post(f"{self.base_url}/orders", json=payload, auth=self._auth(), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def create_payout(self, fund_account_id, amount, currency="INR", mode="NEFT", narration="ATG Payment", reference_id="", notes=None, idempotency_key=""):
        payload = {
            "account_number": self.account_number,
            "fund_account_id": fund_account_id,
            "amount": int(amount),
            "currency": currency,
            "mode": mode,
            "purpose": "payout",
            "queue_if_low_balance": True,
            "reference_id": reference_id,
            "narration": narration,
            "notes": notes or {},
        }
        headers = {"X-Payout-Idempotency": idempotency_key} if idempotency_key else {}
        response = self.session.post(f"{self.base_url}/payouts", json=payload, headers=headers, auth=self._auth(), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def fetch_payout(self, payout_id):
        response = self.session.get(f"{self.base_url}/payouts/{payout_id}", auth=self._auth(), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def verify_signature(self, body, signature, secret=None):
        secret = secret or self.secret
        if not secret or not signature:
            return False
        if not isinstance(body, bytes):
            body = str(body).encode("utf-8")
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)
