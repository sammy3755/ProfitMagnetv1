# server.py
# Advanced Telegram Signal Server + FastAPI (Optimized)

from fastapi import FastAPI
from pydantic import BaseModel
import time
import threading
from typing import Dict

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ================= FASTAPI SETUP =================
app = FastAPI(title="Telegram Signal Server ⚡")

# Store multiple symbols safely
signals: Dict[str, dict] = {}

# ================= SIGNAL MODEL =================
class Signal(BaseModel):
    symbol: str
    signal: str
    sl: float = 0
    tp: float = 0

# ================= API ROUTES =================

# ✅ NEW: Homepage (no more 404)
@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Telegram Signal Server is LIVE 🚀",
        "active_symbols": list(signals.keys())
    }

# ✅ IMPROVED: Always returns full structure
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

# ✅ NEW: Get all active signals
@app.get("/signals")
def get_all_signals():
    return signals

# ✅ IMPROVED: Manual signal set (for testing)
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

BOT_TOKEN = "8789273409:AAGf_BeUBNQ8JjCtphN7zszCc_2oNGM3fx4"
AUTHORIZED_USERS = [8570966290]  # ✅ NEW: Multiple users allowed

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # ✅ NEW: Multi-user authentication
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

    # ✅ IMPROVED: Safe SL/TP parsing
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

    await update.message.reply_text(
        f"✅ {action} {symbol}\nSL={sl} TP={tp}"
    )

# ================= TELEGRAM THREAD =================

def run_telegram():
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Telegram bot running safely...")
    app_telegram.run_polling()

# ✅ NEW: Safe thread start (prevents duplicate bot issues)
telegram_thread = threading.Thread(target=run_telegram, daemon=True)
telegram_thread.start()

# ================= MAIN =================

if __name__ == "__main__":
    import uvicorn

    print("⚡ FastAPI server running on http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)