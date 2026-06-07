import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

CRYPTOBOT_API = settings.cryptobot_api_url
API_KEY = settings.cryptobot_api_key
HEADERS = {"Crypto-Pay-API-Token": API_KEY, "Content-Type": "application/json"}


async def _request(method: str, path: str, **kwargs) -> dict | list | None:
    if not API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.request(method, f"{CRYPTOBOT_API}{path}", headers=HEADERS, **kwargs)
            if resp.status_code != 200:
                logger.warning("CryptoBot API %s %s: HTTP %s — %s", method, path, resp.status_code, resp.text[:200])
                return None
            data = resp.json()
            if data.get("ok"):
                return data.get("result")
            logger.warning("CryptoBot API error: %s", resp.text[:200])
            return None
    except httpx.TimeoutException:
        logger.warning("CryptoBot API timeout: %s %s", method, path)
    except Exception as e:
        logger.warning("CryptoBot API error %s %s: %s", method, path, e)
    return None


async def create_invoice(
    amount: float,
    description: str = "",
    expires_in: int = 3600,
    payload: str = "",
) -> dict | None:
    result = await _request("POST", "/createInvoice", json={
        "asset": "USDT",
        "amount": str(amount),
        "description": description,
        "expires_in": expires_in,
        "payload": payload,
    })
    return result if isinstance(result, dict) else None


async def get_balance() -> float:
    result = await _request("GET", "/getBalance")
    if isinstance(result, list):
        for item in result:
            if item.get("currency_code") == "USDT":
                return float(item.get("available", 0))
    return 0.0


async def transfer(user_id: int, amount: float, spend_id: str) -> dict | None:
    result = await _request("POST", "/transfer", json={
        "user_id": user_id,
        "asset": "USDT",
        "amount": str(amount),
        "spend_id": spend_id,
    })
    return result if isinstance(result, dict) else None


async def get_invoices(
    status: str = "active",
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    result = await _request("GET", "/getInvoices", params={"status": status, "limit": limit, "offset": offset})
    if isinstance(result, dict):
        return result.get("items", [])
    return []

