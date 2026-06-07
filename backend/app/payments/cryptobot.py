import hashlib
import hmac
import time
from decimal import Decimal
from typing import Any

import httpx


class CryptoBotError(Exception):
    pass


class CryptoBotAPI:
    def __init__(self, api_key: str, base_url: str = "https://pay.crypt.bot/api"):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        if not self._api_key:
            raise CryptoBotError("API key not configured")

        url = f"{self._base_url}/{path.lstrip('/')}"
        headers = {
            "Crypto-Pay-API-Token": self._api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.request(method, url, headers=headers, json=json, params=params)
            if resp.status_code != 200:
                raise CryptoBotError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            body = resp.json()
            if not body.get("ok"):
                raise CryptoBotError(body.get("error", {}).get("message", "Unknown error"))
            return body["result"]

    async def create_invoice(
        self,
        amount: Decimal,
        asset: str = "USDT",
        description: str = "",
        expires_in: int = 3600,
        payload: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "amount": str(amount),
            "asset": asset,
            "description": description,
            "expires_in": expires_in,
        }
        if payload:
            body["payload"] = payload
        return await self._request("POST", "createInvoice", json=body)

    async def get_balance(self) -> list[dict[str, Any]]:
        return await self._request("GET", "getBalance")

    async def transfer(
        self,
        user_id: int,
        amount: Decimal,
        asset: str = "USDT",
        spend_id: str | None = None,
    ) -> dict[str, Any]:
        body = {
            "user_id": user_id,
            "amount": str(amount),
            "asset": asset,
            "spend_id": spend_id or f"tgad_{int(time.time())}_{user_id}",
        }
        return await self._request("POST", "transfer", json=body)

    async def get_invoices(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
        invoice_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if invoice_ids:
            params["invoice_ids"] = ",".join(str(i) for i in invoice_ids)
        return await self._request("GET", "getInvoices", params=params)

    @staticmethod
    def verify_webhook_signature(body: bytes, signature: str, api_key: str) -> bool:
        expected = hmac.new(
            api_key.encode(), body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
