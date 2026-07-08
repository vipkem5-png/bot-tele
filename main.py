import threading
import asyncio
from flask import Flask
from bot.config import BOT_TOKEN
from bot.handlers import build_application

# ─── Flask keep-alive server ───────────────────────────────
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot is alive!", 200

def run_flask():
    app_flask.run(host="0.0.0.0", port=8080)

# ─── Telegram bot (polling) ────────────────────────────────
async def run_bot():
    tg_app = build_application(BOT_TOKEN)
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling(drop_pending_updates=True)
    print("✅ Bot đang chạy...")
    
    # Giữ bot chạy mãi
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Flask chạy thread riêng
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    
    # Bot chạy main thread
    asyncio.run(run_bot())
