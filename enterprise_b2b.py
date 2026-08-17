"""
Tozalash Servis - B2B Enterprise & Micro-Profitability Moduli
Phase 18-19: Invoicing, B2B Subscriptions, and Daily P&L (Tasks 171-190)
"""

from loguru import logger
from datetime import datetime


class EnterpriseB2B:
    def __init__(self):
        logger.info("🏢 B2B Enterprise & Invoicing modul yuklanmoqda...")
        self.corporate_subscriptions = {}

    async def generate_invoice(
        self, company_name: str, services: list, total_amount: float
    ):
        """
        B2B mijozlar uchun PDF schet-faktura shakllantirish.
        """
        from invoice_generator import generate_invoice as pdf_generate

        invoice_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        order_data = {
            "id": invoice_id,
            "total_amount": total_amount,
            "items": services,
            "status": "pending"
        }
        client_data = {
            "name": company_name,
            "phone": "B2B Client"
        }
        output_path = f"data/invoices/{invoice_id}.pdf"
        
        await pdf_generate(order_data, client_data, output_path)

        logger.info(
            f"[INVOICE] {company_name} uchun schet-faktura yaratildi: {invoice_id}. Jami sum: {total_amount}"
        )
        return output_path

    async def setup_subscription(self, company_name: str, frequency: str):
        """
        Korporativ abonent to'lovi (Haftalik/Oylik).
        """
        self.corporate_subscriptions[company_name] = frequency
        logger.info(
            f"[B2B] {company_name} kompaniyasi bilan '{frequency}' abonement shartnomasi tuzildi."
        )


class ProfitabilityAnalytics:
    def __init__(self):
        logger.info("💸 Micro-Profitability Analytics modul yuklanmoqda...")
        self.daily_revenue = 0
        self.daily_expenses = 0

    async def calculate_per_order_margin(
        self,
        order_id: int,
        price: float,
        travel_cost: float,
        chemical_cost: float,
        worker_pay: float,
    ):
        """
        Bitta buyurtmadan qoladigan sof foydani hisoblash (Per-Order Margin).
        """
        total_expense = travel_cost + chemical_cost + worker_pay
        margin = price - total_expense

        self.daily_revenue += price
        self.daily_expenses += total_expense

        logger.info(
            f"[PROFIT] Order {order_id}: Daromad = {price}, Xarajatlar = {total_expense}, SOF FOYDA = {margin}"
        )

        if chemical_cost > (price * 0.2):
            logger.warning(
                f"[LEAKAGE ALERT] Order {order_id} da ximikat sarfi normadan oshdi!"
            )

        return margin

    async def generate_daily_pl_report(self):
        """
        Kunlik foyda/zarar hisoboti (P&L Report).
        """
        net_profit = self.daily_revenue - self.daily_expenses
        logger.info(
            f"[DAILY P&L] Kunlik Tushum: {self.daily_revenue}, Xarajatlar: {self.daily_expenses}, Sof Foyda: {net_profit}"
        )
        return {
            "revenue": self.daily_revenue,
            "expenses": self.daily_expenses,
            "net_profit": net_profit,
        }


b2b_manager = EnterpriseB2B()
profit_analytics = ProfitabilityAnalytics()
