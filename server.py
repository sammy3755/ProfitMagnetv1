# server.py
# PRODUCTION-READY Telegram Signal Server ⚡

from fastapi import FastAPI
from pydantic import BaseModel
import time
import threading
import os
from typing import Dict

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ================= FASTAPI SETUP =================
app = FastAPI(title="Telegram Signal Server ⚡")

signals: Dict[str, dict] = {}

# ================= SIGNAL MODEL =================
class Signal(BaseModel):
    symbol: str
    signal: str
    sl: float = 0
    tp: float = 0

# ================= API ROUTES =================

@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Telegram Signal Server is LIVE 🚀",
        "active_symbols": list(signals.keys())
    }

@app.get("/signal")
def get_signal(symbol: str):
    symbol = symbol.upper()

    if symbol not in signals:
        return {
            "symbol": symbol,
            "signal": "none",
            "sl": 0,
            "tp": 0,
            "id": 0
        }

    return signals[symbol]

@app.get("/signals")
def get_all_signals():
    return signals

@app.post("/set")
def set_signal(signal: Signal):
    symbol = signal.symbol.upper()

    signals[symbol] = {
        "symbol": symbol,
        "signal": signal.signal.lower(),
        "sl": signal.sl,
        "tp": signal.tp,
        "id": int(time.time())
    }

    print(f"📡 API Signal Set: {signals[symbol]}")
    return signals[symbol]

# ================= TELEGRAM BOT =================

# 🔐 USE ENV VARIABLES (IMPORTANT FOR HOSTING)
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_USERS = [int(x) for x in os.getenv("AUTHORIZED_USERS", "").split(",") if x]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ Unauthorized user")
        return

    text = update.message.text.upper().strip()
    parts = text.split()

    if len(parts) < 2:
        await update.message.reply_text("❌ Format: BUY XAUUSD SL=2300 TP=2400")
        return

    action = parts[0]
    symbol = parts[1]

    if action not in ["BUY", "SELL", "CLOSE"]:
        await update.message.reply_text("❌ Use BUY / SELL / CLOSE")
        return

    sl = 0
    tp = 0

    for part in parts[2:]:
        try:
            if "SL=" in part:
                sl = float(part.split("=")[1])
            elif "TP=" in part:
                tp = float(part.split("=")[1])
        except:
            pass

    signals[symbol] = {
        "symbol": symbol,
        "signal": action.lower(),
        "sl": sl,
        "tp": tp,
        "id": int(time.time())
    }

    print(f"🔥 Telegram Signal: {signals[symbol]}")

    await update.message.reply_text(f"✅ {action} {symbol}\nSL={sl} TP={tp}")

# ================= TELEGRAM START =================

def run_telegram():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set")
        return

    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Telegram bot running...")
    app_telegram.run_polling()

# ✅ START TELEGRAM SAFELY (FOR HOSTING)
@app.on_event("startup")
async def startup_event():
    threading.Thread(target=run_telegram, daemon=True).start()

# ================= MAIN =================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))  # ✅ dynamic port

    print(f"⚡ Server running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
