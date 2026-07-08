import json
import asyncio
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application

from bot.config import BOT_TOKEN
from bot.handlers import build_application

# Singleton app để tái sử dụng
_app: Application | None = None

async def get_app() -> Application:
    global _app
    if _app is None:
        _app = build_application(BOT_TOKEN)
        await _app.initialize()
    return _app

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            update_data = json.loads(body)
            asyncio.run(self._process(update_data))
            self.send_response(200)
        except Exception as e:
            print(f"Webhook error: {e}")
            self.send_response(500)
        
        self.end_headers()

    async def _process(self, update_data: dict):
        app = await get_app()
        update = Update.de_json(update_data, app.bot)
        await app.process_update(update)

    def log_message(self, *args):
        pass  # tắt log spam
