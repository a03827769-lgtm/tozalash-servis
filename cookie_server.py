import os
import json
from aiohttp import web
from loguru import logger
from dotenv import load_dotenv, set_key

env_path = os.path.join(os.path.dirname(__file__), ".env")

async def handle_update_cookie(request):
    try:
        data = await request.json()
        account_index = data.get("account_index", 1)
        psid = data.get("psid", "")
        psidts = data.get("psidts", "")
        
        logger.info(f"🔄 Kengaytmadan {account_index}-akkaunt uchun yangi Cookie keldi!")
        
        updated = False
        if psid:
            set_key(env_path, f"GEMINI_PSID_{account_index}", psid)
            updated = True
        if psidts:
            set_key(env_path, f"GEMINI_PSIDTS_{account_index}", psidts)
            updated = True
            
        if updated:
            # Rotator xotirasini yangilaymiz (import orqali)
            try:
                from gemini_rotator import rotator
                if rotator.has_accounts:
                    rotator.update_account_cookies(account_index, psid, psidts)
            except Exception as e:
                logger.error(f"Rotatorni yangilashda xato: {e}")
                
            return web.json_response({"status": "success", "message": f"Account {account_index} updated"})
        else:
            return web.json_response({"status": "ignored", "message": "No cookies provided"})
            
    except Exception as e:
        logger.error(f"Cookie server xatosi: {e}")
        return web.json_response({"status": "error"}, status=500)

async def start_cookie_server():
    app = web.Application()
    
    # CORS muammosini hal qilish uchun oddiy ruxsat
    async def cors_middleware(app, handler):
        async def middleware(request):
            if request.method == 'OPTIONS':
                response = web.Response()
            else:
                response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        return middleware
        
    app.middlewares.append(cors_middleware)
    app.router.add_post('/update_cookie', handle_update_cookie)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 9090)
    await site.start()
    logger.success("🌐 Cookie Qabul qiluvchi server ishga tushdi (Port: 9090)")
