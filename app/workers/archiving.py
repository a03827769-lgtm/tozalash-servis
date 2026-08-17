from app.workers.celery_app import celery_app
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timedelta
import asyncio

# Assuming we have a way to get a session in celery tasks (e.g. creating a new engine/sessionmaker)
from app.db.session import AsyncSessionLocal
from app.models.order import Order, OrderArchive
import logging

logger = logging.getLogger(__name__)


async def _archive_old_orders():
    """
    Async logic to archive orders older than 1 year.
    Moves data from 'orders' to 'orders_archive'.
    """
    async with AsyncSessionLocal() as session:
        # Example threshold: 1 year ago (assuming models have created_at)
        # For demonstration, we'll archive all paid orders (status=1)
        # In a real scenario: where(Order.created_at < threshold)

        try:
            result = await session.execute(
                select(Order).where(Order.status == 1).limit(100)
            )
            old_orders = result.scalars().all()

            if not old_orders:
                logger.info("No old orders to archive.")
                return

            archive_records = []
            order_ids_to_delete = []

            for order in old_orders:
                archive_records.append(
                    OrderArchive(
                        original_id=order.id,
                        amount=order.amount,
                        status=order.status,
                        client_name=order.client_name,
                    )
                )
                order_ids_to_delete.append(order.id)

            # 1. Insert into archive
            session.add_all(archive_records)

            # 2. Delete from main table
            await session.execute(
                delete(Order).where(Order.id.in_(order_ids_to_delete))
            )

            # 3. Commit transaction (ACID)
            await session.commit()
            logger.info(f"Successfully archived {len(order_ids_to_delete)} orders.")

        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to archive orders: {e}")


@celery_app.task
def archive_old_orders_task():
    """
    Task 26: Data Archiving.
    This task can be scheduled via Celery Beat (e.g., run every Sunday at 2 AM).
    """
    asyncio.run(_archive_old_orders())
    return "Archiving complete"
