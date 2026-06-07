from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth.deps import get_current_user
from ..models.user import User
from ..models.transaction import Transaction

router = APIRouter()


@router.get("/")
async def list_transactions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
    )
    txns = result.scalars().all()
    return [
        {
            "id": t.id,
            "amount": t.amount,
            "type": t.type,
            "status": t.status,
            "payment_system": t.payment_system,
            "description": t.description,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in txns
    ]
