"""
Tozalash Servis - Google Sheets CRM Integratsiyasi
Barcha buyurtmalar, mijozlar va moliya Google Sheets'da saqlanadi
(Robust error handling & Rate Limiting protection added)
"""

import json
import time
from functools import wraps
from datetime import datetime
from typing import List, Dict, Optional
import gspread
from google.oauth2.service_account import Credentials
from loguru import logger

from config import GOOGLE_SHEETS_ID, GOOGLE_CREDENTIALS_FILE, SHEETS, BUSINESS_NAME

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def retry_on_exception(max_retries=3, backoff_factor=2):
    """Network errors va API Rate Limit (429) dan himoya qiluvchi decorator"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if "429" in str(e) or "Quota" in str(e):
                        sleep_time = backoff_factor ** (
                            retries + 2
                        )  # API limit uchun ko'proq kutish
                        logger.warning(
                            f"⚠️ API Rate Limit in {func.__name__}: Retrying in {sleep_time}s..."
                        )
                    else:
                        sleep_time = backoff_factor**retries
                        logger.warning(
                            f"⚠️ Error in {func.__name__}: {e}. Retrying in {sleep_time}s..."
                        )

                    if retries == max_retries:
                        logger.error(f"❌ Max retries reached for {func.__name__}: {e}")
                        raise e
                    time.sleep(sleep_time)

        return wrapper

    return decorator


class GoogleSheetsCRM:
    """Google Sheets CRM tizimi"""

    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self._connect()

    @retry_on_exception(max_retries=4)
    def _connect(self):
        """Google Sheets'ga ulanish"""
        try:
            creds = Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(GOOGLE_SHEETS_ID)
            logger.info("✅ Google Sheets'ga muvaffaqiyatli ulandi")
        except Exception as e:
            logger.error(f"Google Sheets ulanish xatosi: {e}")
            raise e

    @retry_on_exception(max_retries=3)
    def _get_sheet(self, sheet_name: str):
        """Varaqni olish"""
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Varaq yo'q bo'lsa yaratish
            sheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=30)
            self._setup_sheet_headers(sheet, sheet_name)
            return sheet

    def _setup_sheet_headers(self, sheet, sheet_name: str):
        """Varaq sarlavhalarini o'rnatish"""
        headers = {
            SHEETS["orders"]: [
                "№",
                "Buyurtma Raqami",
                "Mijoz",
                "Telefon",
                "Xizmat",
                "Manzil",
                "Sana",
                "Miqdor",
                "Birlik",
                "Narx/birlik",
                "Jami",
                "Ishchi",
                "Holat",
                "To'lov",
                "Yaratilgan",
            ],
            SHEETS["clients"]: [
                "№",
                "Telegram ID",
                "Ism",
                "Telefon",
                "Til",
                "Shahar",
                "Jami Buyurtma",
                "Jami Sarflangan",
                "Reyting",
                "Oxirgi Faollik",
            ],
            SHEETS["workers"]: [
                "№",
                "Ism",
                "Telefon",
                "Telegram ID",
                "Mutaxassislik",
                "Faol",
                "Jami Ish",
                "Oylik Ish haqi",
                "Reyting",
            ],
            SHEETS["finance"]: [
                "Sana",
                "Tur",
                "Kategoriya",
                "Summa",
                "Tavsif",
                "Buyurtma №",
            ],
            SHEETS["dashboard"]: ["Ko'rsatkich", "Bugun", "Bu Oy", "Jami"],
            SHEETS["ai_log"]: [
                "Sana",
                "Tur",
                "Ma'lumot",
                "Natija",
                "Muvaffaqiyat",
                "Yaxshilanish",
            ],
            SHEETS["competitors"]: [
                "Nomi",
                "Platforma",
                "URL",
                "Telefon",
                "Narxlar",
                "Kuchli Tomonlar",
                "Zaif Tomonlar",
                "Tekshirilgan",
            ],
            SHEETS["learning"]: ["Sana", "Tur", "Kirish", "Chiqish", "Ball", "Tavsif"],
        }

        sheet_headers = headers.get(sheet_name, ["Ustun 1", "Ustun 2"])
        sheet.insert_row(sheet_headers, 1)

        sheet.format(
            "1:1",
            {
                "backgroundColor": {"red": 0.18, "green": 0.47, "blue": 0.82},
                "textFormat": {
                    "bold": True,
                    "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                },
                "horizontalAlignment": "CENTER",
            },
        )

    def setup_all_sheets(self):
        for sheet_key, sheet_name in SHEETS.items():
            try:
                sheet = self._get_sheet(sheet_name)
                logger.info(f"✅ Varaq tayyor: {sheet_name}")
            except Exception as e:
                logger.error(f"Varaq xatosi {sheet_name}: {e}")

        self._setup_dashboard()
        logger.info("✅ Google Sheets CRM to'liq sozlandi!")

    @retry_on_exception(max_retries=3)
    def _setup_dashboard(self):
        try:
            sheet = self._get_sheet(SHEETS["dashboard"])
            rows = [
                ["📊 KO'RSATKICHLAR", "BUGUN", "BU OY", "JAMI"],
                [
                    "💰 Daromad (so'm)",
                    "=SUM(Moliya!B:B)",
                    '=SUMIF(Moliya!A:A,TEXT(TODAY(),"YYYY-MM")&"*",Moliya!B:B)',
                    "=SUM(Moliya!B:B)",
                ],
                [
                    "📦 Buyurtmalar soni",
                    "=COUNTIF(Buyurtmalar!N:N,TODAY())",
                    "",
                    "=COUNTA(Buyurtmalar!A:A)-1",
                ],
                ["✅ Bajarilgan", "", "", '=COUNTIF(Buyurtmalar!M:M,"bajarildi")'],
                ["👥 Yangi mijozlar", "", "", "=COUNTA(Mijozlar!A:A)-1"],
                ["⭐ O'rtacha reyting", "", "", "=AVERAGE(Mijozlar!H:H)"],
            ]

            for i, row in enumerate(rows, start=1):
                sheet.insert_row(row, i)
        except Exception as e:
            logger.error(f"Dashboard xatosi: {e}")
            raise e

    @retry_on_exception(max_retries=3)
    def add_order(self, order: Dict, client: Dict, worker_name: str = ""):
        try:
            sheet = self._get_sheet(SHEETS["orders"])
            all_rows = sheet.get_all_values()
            row_num = len(all_rows)

            row = [
                row_num,
                order.get("order_number", ""),
                client.get("name", ""),
                client.get("phone", ""),
                order.get("service_name", ""),
                order.get("address", ""),
                order.get("scheduled_date", ""),
                order.get("quantity", ""),
                order.get("unit", ""),
                f"{order.get('price_per_unit', 0):,}",
                f"{order.get('total_price', 0):,}",
                worker_name,
                order.get("status", "yangi"),
                order.get("payment_status", "kutilmoqda"),
                datetime.now().strftime("%Y-%m-%d %H:%M"),
            ]
            sheet.append_row(row)
            logger.info(
                f"✅ Buyurtma Google Sheets'ga qo'shildi: #{order.get('order_number')}"
            )
        except Exception as e:
            logger.error(f"Google Sheets buyurtma qo'shish xatosi: {e}")
            raise e

    @retry_on_exception(max_retries=3)
    def update_order_status_in_sheets(self, order_number: str, status: str):
        try:
            sheet = self._get_sheet(SHEETS["orders"])
            cell = sheet.find(order_number)
            if cell:
                sheet.update_cell(cell.row, 13, status)
        except Exception as e:
            logger.error(f"Sheets buyurtma yangilash xatosi: {e}")
            raise e

    @retry_on_exception(max_retries=3)
    def add_or_update_client(self, client: Dict):
        try:
            sheet = self._get_sheet(SHEETS["clients"])
            try:
                cell = sheet.find(str(client.get("telegram_id", "")))
                if cell:
                    row = cell.row
                    sheet.update_cell(row, 7, client.get("total_orders", 0))
                    sheet.update_cell(row, 8, f"{client.get('total_spent', 0):,}")
                    sheet.update_cell(row, 10, datetime.now().strftime("%Y-%m-%d"))
                    return
            except Exception as e:
                logger.debug(
                    f"Sheets da mijoz '{client.get('telegram_id')}' topilmadi (yangi qator yaratiladi): {e}"
                )

            all_rows = sheet.get_all_values()
            row_num = len(all_rows)
            row = [
                row_num,
                client.get("telegram_id", ""),
                client.get("name", ""),
                client.get("phone", ""),
                client.get("language", "uz"),
                client.get("city", "Toshkent"),
                client.get("total_orders", 0),
                f"{client.get('total_spent', 0):,}",
                client.get("rating", 5.0),
                datetime.now().strftime("%Y-%m-%d"),
            ]
            sheet.append_row(row)
        except Exception as e:
            logger.error(f"Sheets mijoz xatosi: {e}")
            raise e

    @retry_on_exception(max_retries=2)
    def log_ai_activity(
        self,
        activity_type: str,
        data: str,
        result: str,
        success: bool,
        improvement: str = "",
    ):
        try:
            sheet = self._get_sheet(SHEETS["ai_log"])
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                activity_type,
                data[:500] if data else "",
                result[:500] if result else "",
                "✅" if success else "❌",
                improvement,
            ]
            sheet.append_row(row)
        except Exception as e:
            logger.error(f"AI log xatosi: {e}")
            raise e

    @retry_on_exception(max_retries=2)
    def update_competitor(self, competitor: Dict):
        try:
            sheet = self._get_sheet(SHEETS["competitors"])
            try:
                cell = sheet.find(competitor.get("name", ""))
                if cell:
                    row = cell.row
                    sheet.update_cell(row, 5, competitor.get("price_info", ""))
                    sheet.update_cell(row, 6, competitor.get("strengths", ""))
                    sheet.update_cell(row, 7, competitor.get("weaknesses", ""))
                    sheet.update_cell(row, 8, datetime.now().strftime("%Y-%m-%d"))
                    return
            except Exception as e:
                logger.debug(
                    f"Sheets da raqib '{competitor.get('name')}' topilmadi (yangi qator yaratiladi): {e}"
                )

            row = [
                competitor.get("name", ""),
                competitor.get("platform", ""),
                competitor.get("url", ""),
                competitor.get("phone", ""),
                competitor.get("price_info", ""),
                competitor.get("strengths", ""),
                competitor.get("weaknesses", ""),
                datetime.now().strftime("%Y-%m-%d"),
            ]
            sheet.append_row(row)
        except Exception as e:
            logger.error(f"Raqib yangilash xatosi: {e}")
            raise e

    @retry_on_exception(max_retries=3)
    def get_dashboard_data(self) -> Dict:
        try:
            orders_sheet = self._get_sheet(SHEETS["orders"])
            all_orders = orders_sheet.get_all_records()

            today = datetime.now().strftime("%Y-%m-%d")
            today_orders = [
                o for o in all_orders if str(o.get("Yaratilgan", "")).startswith(today)
            ]

            return {
                "total_orders": len(all_orders),
                "today_orders": len(today_orders),
                "today_revenue": sum(
                    float(str(o.get("Jami", "0")).replace(",", ""))
                    for o in today_orders
                ),
            }
        except Exception as e:
            logger.error(f"Dashboard ma'lumot xatosi: {e}")
            raise e


sheets_crm = None


def get_sheets_crm():
    global sheets_crm
    if sheets_crm is None:
        sheets_crm = GoogleSheetsCRM()
    return sheets_crm
