from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.transaction import Transaction
from app.models.payment_invoice import PaymentInvoice
from app.models.withdraw_request import WithdrawRequest
from app.payments.cryptobot import CryptoBotAPI, CryptoBotError


class InsufficientBalanceError(Exception):
    pass


class PaymentService:
    def __init__(self, db: AsyncSession, cryptobot: CryptoBotAPI):
        self.db = db
        self.cryptobot = cryptobot

    async def create_deposit_invoice(
        self, user: User, amount: float, asset: str = "USDT"
    ) -> dict:
        payload = str(uuid4())
        result = await self.cryptobot.create_invoice(
            amount=Decimal(str(amount)),
            asset=asset,
            description=f"Deposit for user #{user.id}",
            payload=payload,
        )

        invoice = PaymentInvoice(
            user_id=user.id,
            amount=float(result["amount"]),
            asset=result.get("asset", asset),
            crypto_bot_invoice_id=result["invoice_id"],
            payload=payload,
            pay_url=result.get("pay_url"),
        )
        self.db.add(invoice)
        await self.db.flush()

        return {
            "pay_url": result["pay_url"],
            "invoice_id": result["invoice_id"],
        }

    async def process_deposit_webhook(self, payload: dict) -> None:
        invoice_id = payload.get("invoice_id")
        status = payload.get("status")

        if not invoice_id or not status:
            return

        result = await self.db.execute(
            select(PaymentInvoice).where(
                PaymentInvoice.crypto_bot_invoice_id == int(invoice_id)
            )
        )
        invoice = result.scalar_one_or_none()

        if not invoice or invoice.status != "pending":
            return

        if status == "paid":
            amount = float(payload.get("amount", 0))
            asset = payload.get("asset", "USDT")
            rub_amount = round(amount * settings.cryptobot_usdt_rate, 2)

            user_result = await self.db.execute(
                select(User).where(User.id == invoice.user_id).with_for_update()
            )
            user = user_result.scalar_one_or_none()
            if not user:
                return

            user.balance_rub += rub_amount
            invoice.status = "paid"

            self.db.add(Transaction(
                user_id=user.id,
                amount=rub_amount,
                type="deposit",
                status="completed",
                external_id=str(invoice_id),
                payment_system="cryptobot",
                description=f"Deposit {rub_amount} RUB ({amount} {asset}) via CryptoBot",
            ))
        elif status in ("expired", "cancelled"):
            invoice.status = status

    async def check_invoice(self, invoice_id: int, user_id: int) -> dict:
        result = await self.db.execute(
            select(PaymentInvoice).where(
                PaymentInvoice.crypto_bot_invoice_id == invoice_id,
                PaymentInvoice.user_id == user_id,
            )
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            return {"paid": False, "error": "Invoice not found"}

        if invoice.status == "paid":
            return {"paid": True, "amount": invoice.amount}
        elif invoice.status == "expired":
            return {"paid": False, "status": "expired"}

        try:
            invoices = await self.cryptobot.get_invoices(invoice_ids=[invoice_id])
        except CryptoBotError:
            return {"paid": False, "status": invoice.status}

        if not invoices:
            return {"paid": False, "status": invoice.status}

        cb_invoice = invoices[0]
        cb_status = cb_invoice.get("status")

        if cb_status == "paid" and invoice.status == "pending":
            await self.process_deposit_webhook(cb_invoice)

        return {
            "paid": cb_status == "paid",
            "status": cb_status,
        }

    async def process_withdraw(self, user: User, amount: float, asset: str = "USDT") -> WithdrawRequest:
        user_result = await self.db.execute(
            select(User).where(User.id == user.id).with_for_update()
        )
        user_db = user_result.scalar_one_or_none()
        if not user_db:
            raise InsufficientBalanceError("User not found")

        if user_db.balance_rub < amount:
            raise InsufficientBalanceError(
                f"Insufficient balance: {user_db.balance_rub} < {amount}"
            )

        usdt_amount = round(amount / settings.cryptobot_usdt_rate, 2)
        fee = round(amount * settings.commission_rate, 2)
        net_amount = amount - fee

        user_db.balance_rub -= amount

        withdrawal = WithdrawRequest(
            user_id=user.id,
            amount=amount,
            fee=fee,
            net_amount=net_amount,
            asset=asset,
            destination_type="cryptobot",
            status="pending",
        )
        self.db.add(withdrawal)
        await self.db.flush()

        self.db.add(Transaction(
            user_id=user.id,
            amount=-amount,
            type="withdraw",
            status="pending",
            external_id=f"wd_{withdrawal.id}",
            description=f"Withdraw request #{withdrawal.id}: {amount} RUB",
        ))

        try:
            spend_id = str(uuid4())
            result = await self.cryptobot.transfer(
                user_id=user.id,
                amount=Decimal(str(usdt_amount)),
                asset=asset,
                spend_id=spend_id,
            )
            withdrawal.crypto_bot_transfer_id = result.get("transfer_id", str(spend_id))
            withdrawal.status = "completed"
        except CryptoBotError:
            withdrawal.status = "failed"
            user_db.balance_rub += amount

        return withdrawal
