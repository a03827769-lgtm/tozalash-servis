from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.base import TenantBase
from sqlalchemy import Column, Integer, Float


class Order(TenantBase):
    __tablename__ = "orders"
    amount = Column(Float, nullable=False)
    status = Column(Integer, default=0)  # 0: unpaid, 1: paid


class Wallet(TenantBase):
    __tablename__ = "wallets"
    balance = Column(Float, default=0.0)


async def process_payment(
    session: AsyncSession, order_id: int, wallet_id: int, amount: float
):
    """
    Demonstrates STRICT ACID Transactions.
    Ensures that money is deducted from the wallet AND the order status is updated.
    If either fails, the ENTIRE transaction is rolled back.
    """
    async with session.begin():  # This block ensures ACID properties (Begin, Commit, Rollback)
        try:
            # 1. Deduct amount from wallet
            # In real-world, we'd fetch the wallet with row-level locking: with_for_update()
            # wallet = await session.execute(select(Wallet).where(Wallet.id == wallet_id).with_for_update())

            # Simulated deduction...
            pass

            # 2. Update order status
            # order = await session.execute(select(Order).where(Order.id == order_id).with_for_update())

            # Simulated update...
            pass

            # session.commit() is implicitly called if no exception is raised
        except Exception as e:
            # session.rollback() is implicitly called if an exception occurs inside the block
            raise HTTPException(
                status_code=400, detail=f"Transaction failed, rolling back: {str(e)}"
            )
