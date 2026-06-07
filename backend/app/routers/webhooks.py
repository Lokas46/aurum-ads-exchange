from fastapi import APIRouter, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import async_session
from ..payments.cryptobot import CryptoBotAPI
from ..payments.service import PaymentService

router = APIRouter()


@router.post("/cryptobot")
async def cryptobot_webhook(request: Request):
    body_bytes = await request.body()
    signature = request.headers.get("Crypto-Pay-API-Signature", "")

    if not CryptoBotAPI.verify_webhook_signature(
        body_bytes, signature, settings.cryptobot_api_key
    ):
        return Response(status_code=403)

    payload = await request.json()

    async with async_session() as session:
        cryptobot = CryptoBotAPI(settings.cryptobot_api_key, settings.cryptobot_api_url)
        service = PaymentService(session, cryptobot)
        await service.process_deposit_webhook(payload)
        await session.commit()

    return {"ok": True}
