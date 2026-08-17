import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from config import BUSINESS_PHONE


async def start_scheduler(
    content_manager,
    competitor_analyzer,
    daily_report_system,
    self_learning_system,
    workers_manager,
    profit_analytics,
    voice_agent,
    stop_event: asyncio.Event = None,
):
    """
    Barcha fon vazifalarini APScheduler orqali rejalashtirish.

    Args:
        stop_event: Bu event set bo'lganda scheduler to'xtaydi.
                    None bo'lsa, jarayon to'xtatilguncha ishlaydi.
    """
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    # 1. Kontent manager (Telegram kanal uchun kunlik postlar)
    scheduler.add_job(
        content_manager.telegram.post_to_channel,
        "cron",
        args=["promo"],
        hour="9,13,17,20",
        minute=0,
        id="channel_posts",
        replace_existing=True,
    )

    # 2. Raqiblar tahlili (Har kuni 08:00)
    scheduler.add_job(
        competitor_analyzer.analyze_all_competitors,
        "cron",
        hour=8,
        minute=0,
        id="competitor_analysis",
        replace_existing=True,
    )

    # 3. Google Search orqali raqobatchilar (Haftada bir marta, Dushanba 09:00)
    try:
        from bot.services.search import search_competitors

        scheduler.add_job(
            search_competitors,
            "cron",
            day_of_week="mon",
            hour=9,
            minute=0,
            id="google_competitor_search",
            replace_existing=True,
        )
    except ImportError:
        logger.warning(
            "bot.services.search topilmadi, raqobatchilar Google'dan tahlil qilinmaydi."
        )

    # 4. Haftalik hisobot (Dushanba 09:30 — Google bilan bir vaqtda emas)
    scheduler.add_job(
        competitor_analyzer.send_weekly_report,
        "cron",
        day_of_week="mon",
        hour=9,
        minute=30,
        id="weekly_report",
        replace_existing=True,
    )

    # 5. Kunlik hisobot (Har kuni 21:00)
    scheduler.add_job(
        daily_report_system.generate_and_send_report,
        "cron",
        hour=21,
        minute=0,
        id="daily_report",
        replace_existing=True,
    )

    # 6. O'z-o'zini o'rganish (Har kuni 03:00)
    try:
        from daily_optimizer import optimize_guidelines

        scheduler.add_job(
            optimize_guidelines,
            "cron",
            hour=3,
            minute=0,
            id="self_learning",
            replace_existing=True,
        )
    except ImportError:
        logger.warning("daily_optimizer topilmadi.")

    # 7. Eski sessiyalarni tozalash/arxivlash (Har kuni 04:00)
    from database import db
    scheduler.add_job(
        db.archive_old_sessions,
        "cron",
        args=[7], # 7 kundan oshgan
        hour=4,
        minute=0,
        id="archive_sessions",
        replace_existing=True,
    )

    # 7. Ishchilar maoshi hisoboti (Har oyning 28-kuni 20:00)
    scheduler.add_job(
        workers_manager.send_salary_report,
        "cron",
        day=28,
        hour=20,
        minute=0,
        id="salary_report",
        replace_existing=True,
    )

    # 8. P&L Micro-Profitability hisoboti (Har kuni 23:50)
    scheduler.add_job(
        profit_analytics.generate_daily_pl_report,
        "cron",
        hour=23,
        minute=50,
        id="pl_report",
        replace_existing=True,
    )

    # 9. Abandoned Cart qo'ng'iroqlari (Har kuni 12:00)
    scheduler.add_job(
        voice_agent.make_outbound_call,
        "cron",
        args=[BUSINESS_PHONE, "abandoned_cart"],
        hour=12,
        minute=0,
        id="abandoned_cart",
        replace_existing=True,
    )

    # 10. Autonomous Web Researcher (Raqobatchilar narxlarini har kuni 04:00 da yig'ish)
    try:
        from web_researcher import run_researcher
        scheduler.add_job(
            run_researcher,
            "cron",
            hour=4,
            minute=0,
            id="autonomous_web_researcher",
            replace_existing=True,
        )
    except ImportError:
        logger.warning("web_researcher topilmadi, narx monitoringi ishlamaydi.")

    scheduler.start()
    logger.info("✅ APScheduler barcha vazifalarni rejalashtirdi")

    # M4 FIX: while True + sleep(3600) anti-pattern o'rniga Event-based kutish
    if stop_event is None:
        stop_event = asyncio.Event()

    try:
        await stop_event.wait()
    finally:
        scheduler.shutdown(wait=False)
        logger.info("🛑 APScheduler to'xtatildi")
