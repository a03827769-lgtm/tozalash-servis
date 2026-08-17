import os
import io
import asyncio
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from database import db
from loguru import logger


class ChartGenerator:
    def __init__(self):
        os.makedirs("reports", exist_ok=True)

    async def generate_revenue_chart(self, custom_db=None) -> str:
        """Oxirgi 30 kunlik daromad grafigini chizish va rasmga saqlash"""
        try:
            target_db = custom_db or db
            if target_db.db_type == "postgres":
                sql = """
                    SELECT DATE(created_at) as date, COALESCE(SUM(total_price), 0) as daily_revenue, COUNT(id) as daily_orders
                    FROM orders
                    WHERE created_at >= (CURRENT_TIMESTAMP - INTERVAL '30 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """
            else:
                sql = """
                    SELECT DATE(created_at) as date, COALESCE(SUM(total_price), 0) as daily_revenue, COUNT(id) as daily_orders
                    FROM orders
                    WHERE created_at >= DATETIME('now', '-30 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """
            data = await target_db.fetch_all(sql)

            if not data:
                return None

            dates = [row["date"] for row in data]
            revenues = [row["daily_revenue"] or 0 for row in data]
            orders = [row["daily_orders"] or 0 for row in data]

            fig, ax1 = plt.subplots(figsize=(10, 6))

            color = "tab:blue"
            ax1.set_xlabel("Sana")
            ax1.set_ylabel("Daromad (so'm)", color=color)
            ax1.plot(
                dates, revenues, color=color, marker="o", linewidth=2, label="Daromad"
            )
            ax1.tick_params(axis="y", labelcolor=color)
            ax1.grid(True, linestyle="--", alpha=0.7)

            ax2 = ax1.twinx()
            color = "tab:red"
            ax2.set_ylabel("Buyurtmalar soni", color=color)
            ax2.bar(dates, orders, color=color, alpha=0.3, label="Buyurtmalar")
            ax2.tick_params(axis="y", labelcolor=color)

            # X o'qini to'g'irlash
            fig.autofmt_xdate()
            plt.title("Oxirgi 30 kunlik daromad va buyurtmalar statistikasi")

            fig.tight_layout()

            filepath = f"reports/revenue_chart_{int(datetime.now().timestamp())}.png"
            plt.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close(fig)

            return filepath

        except Exception as e:
            logger.error(f"Grafik chizishda xato: {e}")
            return None


chart_generator = ChartGenerator()
