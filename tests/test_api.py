import httpx
import pytest

BASE = "http://localhost:8001"


@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_channels_list():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/channels")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_all_channels():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/channels/all")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_payment_methods():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/payments/methods")
        assert r.status_code == 200
        methods = r.json()
        assert isinstance(methods, list)
        assert any(m["id"] == "cryptobot" for m in methods)


@pytest.mark.asyncio
async def test_user_register():
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/api/users/register", json={
            "id": 999999999,
            "username": "test_user",
            "first_name": "Test",
        })
        assert r.status_code == 200
        assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_user_balance():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/users/999999999/balance")
        assert r.status_code == 200
        data = r.json()
        assert "balance" in data


@pytest.mark.asyncio
async def test_admin_cryptobot_setup_unauthorized():
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/api/admin/cryptobot-setup")
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_cryptobot_balance_unauthorized():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/admin/cryptobot-balance")
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_miniapp_served():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/miniapp/")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
