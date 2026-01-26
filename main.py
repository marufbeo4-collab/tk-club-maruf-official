import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from threading import Thread
from typing import Dict, Optional

import requests
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# =========================
# YOUR CONFIG (AS YOU GAVE)
# =========================
BOT_TOKEN = "8456002611:AAHZUGRB6VEPGwimGwpusCXuUSMS7yL2XTY"

BRAND_NAME = "⚡ TK MARUF OFFICIAL 24/7 SIGNAL"
CHANNEL_LINK = "https://t.me/big_maruf_official0"

# Targets
TARGETS = {
    "MAIN_GROUP": -1003263928753,
}

# =========================
# API (NEW)
# =========================
WINGO_API = "https://api880.inpay88.net/api/webapi/GetNoaverageEmerdList"
TYPEID_30S = 5
TYPEID_1M = 1

# =========================
# SETTINGS
# =========================
BD_TZ = timezone(timedelta(hours=6))
MAX_RECOVERY_STEPS = 8
LOOP_SLEEP_30S = 0.60
LOOP_SLEEP_1M = 1.20
FETCH_TIMEOUT = 8

# =========================
# OPTIONAL: PASSWORD LOCK (STATIC)
# (তুমি চাইলে এটাকে বদলাবে)
# =========================
BOT_PASSWORD = "2222"

# =========================
# STICKERS (KEEP EMPTY IF YOU DON'T NEED)
# (এখানে তোমার আগের sticker system বসাতে পারো)
# =========================
STICKERS = {
    "PRED_BIG": None,
    "PRED_SMALL": None,
    "WIN": None,
    "LOSS": None,
}

# =========================
# FLASK KEEP ALIVE
# =========================
app = Flask("")

@app.route("/")
def home():
    return "ALIVE"

def run_http():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_http, daemon=True)
    t.start()

# =========================
# HELPERS
# =========================
def now_bd() -> str:
    return datetime.now(BD_TZ).strftime("%H:%M:%S")

def mode_label(mode: str) -> str:
    return "30 Seconds" if mode == "30S" else "1 Minute"

def safe_int(x, default=0):
    try:
        return int(x)
    except:
        return default

async def safe_delete(bot, chat_id: int, msg_id: int):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
        pass

async def safe_send_sticker(bot, chat_id: int, sticker_id: Optional[str]):
    if not sticker_id:
        return
    try:
        await bot.send_sticker(chat_id, sticker_id)
    except Exception:
        pass

# =========================
# API FETCH (POST)
# =========================
def _fetch_latest_sync(mode: str) -> Optional[dict]:
    type_id = TYPEID_30S if mode == "30S" else TYPEID_1M

    payload = {
        "typeId": type_id,
        "pageSize": 1,
        "pageNo": 1,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    try:
        r = requests.post(WINGO_API, data=payload, headers=headers, timeout=FETCH_TIMEOUT)
        if r.status_code != 200:
            return None

        js = r.json()
        lst = (js.get("data") or {}).get("list") or []
        if not lst:
            return None

        row = lst[0]
        issue = str(row.get("issueNumber") or "")
        num = safe_int(row.get("number"), -1)
        if not issue or num < 0:
            return None

        return {
            "issueNumber": issue,
            "number": num,
            "resultType": "BIG" if num >= 5 else "SMALL",
        }
    except Exception:
        return None

async def fetch_latest(mode: str) -> Optional[dict]:
    return await asyncio.to_thread(_fetch_latest_sync, mode)

# =========================
# PREDICTION ENGINE (SIMPLE BASE)
# (তুমি চাইলে তোমার logic এখানে বসাবে)
# =========================
class PredictionEngine:
    def __init__(self):
        self.history = []      # ["BIG","SMALL"...] newest first
        self.raw_history = []  # raw rows newest first
        self.last_prediction = None

    def update_history(self, latest: dict):
        res = latest["resultType"]
        issue = latest["issueNumber"]

        if not self.raw_history or self.raw_history[0]["issueNumber"] != issue:
            self.history.insert(0, res)
            self.raw_history.insert(0, latest)
            self.history = self.history[:120]
            self.raw_history = self.raw_history[:120]

    def get_pattern_signal(self, current_streak_loss: int) -> str:
        # safe fallback
        if len(self.history) < 6:
            pred = random.choice(["BIG", "SMALL"])
            self.last_prediction = pred
            return pred

        # very simple trend + anti-loss
        last = self.history[0]
        if current_streak_loss >= 2:
            pred = "SMALL" if last == "BIG" else "BIG"
        else:
            pred = last

        self.last_prediction = pred
        return pred

    def confidence(self, streak_loss: int) -> int:
        base = random.randint(86, 93)
        if streak_loss >= 2:
            base = max(80, base - 2)
        return base

# =========================
# STATE
# =========================
@dataclass
class ActiveBet:
    predicted_issue: str
    pick: str
    checking_msg_id: Optional[int] = None

@dataclass
class BotState:
    running: bool = False
    mode: str = "30S"
    session_id: int = 0

    unlocked_users: set = field(default_factory=set)

    engine: PredictionEngine = field(default_factory=PredictionEngine)
    active_bet: Optional[ActiveBet] = None

    last_result_issue: Optional[str] = None
    last_signal_issue: Optional[str] = None

    wins: int = 0
    losses: int = 0
    streak_win: int = 0
    streak_loss: int = 0
    max_win_streak: int = 0
    max_loss_streak: int = 0

state = BotState()

TARGET_CHAT_ID = TARGETS["MAIN_GROUP"]

# =========================
# MESSAGE FORMAT (PREMIUM)
# =========================
def pick_block(pick: str) -> str:
    if pick == "BIG":
        return "🟢🟢 <b>BIG</b> 🟢🟢"
    return "🔴🔴 <b>SMALL</b> 🔴🔴"

def recovery_text() -> str:
    if state.streak_loss <= 0:
        return f"0 Step / {MAX_RECOVERY_STEPS}"
    return f"{state.streak_loss} Step Loss / {MAX_RECOVERY_STEPS}"

def signal_text(next_issue: str, pick: str, conf: int) -> str:
    return (
        f"<b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"🧾 <b>Period:</b> <code>{next_issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>PREDICTION</b> ➜ {pick_block(pick)}\n"
        f"📈 <b>Confidence</b> ➜ <b>{conf}%</b>\n"
        f"🧠 <b>Tracker</b> ➜ <b>{recovery_text()}</b>\n"
        f"⏱ <b>BD Time</b> ➜ <b>{now_bd()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>JOIN</b> ➜ <a href='{CHANNEL_LINK}'>{CHANNEL_LINK}</a>"
    )

def checking_text(wait_issue: str) -> str:
    return (
        f"🛰 <b>CHECKING...</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"🧾 <b>Waiting Period:</b> <code>{wait_issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ syncing result..."
    )

def result_text(issue: str, num: int, res_type: str, pick: str, win: bool) -> str:
    header = "✅ <b>WIN</b> ✅" if win else "❌ <b>LOSS</b> ❌"
    res_emoji = "🟢" if res_type == "BIG" else "🔴"

    return (
        f"{header}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{num} ({res_type})</b>\n"
        f"🎯 <b>Your Pick:</b> {pick_block(pick)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 <b>Tracker</b> ➜ <b>{recovery_text()}</b>\n"
        f"📊 <b>W:</b> <b>{state.wins}</b> | <b>L:</b> <b>{state.losses}</b> | ⏱ <b>{now_bd()}</b>"
    )

def summary_text() -> str:
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"📦 <b>Total:</b> <b>{total}</b>\n"
        f"✅ <b>Win:</b> <b>{state.wins}</b>\n"
        f"❌ <b>Loss:</b> <b>{state.losses}</b>\n"
        f"🎯 <b>Win Rate:</b> <b>{wr:.1f}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>Max Win Streak:</b> <b>{state.max_win_streak}</b>\n"
        f"🧊 <b>Max Loss Streak:</b> <b>{state.max_loss_streak}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>REJOIN</b> ➜ <a href='{CHANNEL_LINK}'>{CHANNEL_LINK}</a>"
    )

# =========================
# MENU UI
# =========================
def main_menu() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("⚡ Start 30 Seconds", callback_data="START:30S"),
            InlineKeyboardButton("⚡ Start 1 Minute", callback_data="START:1M"),
        ],
        [
            InlineKeyboardButton("🛑 Stop & Summary", callback_data="STOP"),
        ],
        [
            InlineKeyboardButton("🔄 Refresh Panel", callback_data="REFRESH"),
        ],
    ]
    return InlineKeyboardMarkup(rows)

def panel_text() -> str:
    status = "🟢 RUNNING" if state.running else "🔴 STOPPED"
    return (
        f"🔐 <b>CONTROL PANEL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Status:</b> {status}\n"
        f"⚡ <b>Mode:</b> <b>{mode_label(state.mode)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Stats</b>\n"
        f"✅ Win: <b>{state.wins}</b>\n"
        f"❌ Loss: <b>{state.losses}</b>\n"
        f"🔥 WinStreak: <b>{state.streak_win}</b>\n"
        f"🧊 LossStep: <b>{state.streak_loss} / {MAX_RECOVERY_STEPS}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>BD Time:</b> <b>{now_bd()}</b>"
    )

# =========================
# SESSION CONTROL
# =========================
def reset_stats():
    state.wins = state.losses = 0
    state.streak_win = state.streak_loss = 0
    state.max_win_streak = state.max_loss_streak = 0

async def stop_session(bot):
    # hard stop before sending anything new
    state.session_id += 1
    state.running = False

    # delete checking if exists
    if state.active_bet and state.active_bet.checking_msg_id:
        await safe_delete(bot, TARGET_CHAT_ID, state.active_bet.checking_msg_id)

    state.active_bet = None
    state.last_signal_issue = None
    state.last_result_issue = None

    await bot.send_message(
        TARGET_CHAT_ID,
        summary_text(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

async def start_session(bot, mode: str):
    state.session_id += 1
    state.running = True
    state.mode = mode

    state.engine = PredictionEngine()
    state.active_bet = None
    state.last_signal_issue = None
    state.last_result_issue = None
    reset_stats()

    await bot.send_message(
        TARGET_CHAT_ID,
        f"✅ <b>CONNECTED</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Mode: <b>{mode_label(mode)}</b>\n"
        f"⏱ {now_bd()}",
        parse_mode=ParseMode.HTML
    )

# =========================
# ENGINE LOOP (NO SKIP, NO GHOST FEEDBACK)
# =========================
async def engine_loop(context: ContextTypes.DEFAULT_TYPE, my_session: int):
    bot = context.bot

    while state.running and state.session_id == my_session:
        latest = await fetch_latest(state.mode)
        if not latest:
            await asyncio.sleep(0.35)
            continue

        issue = latest["issueNumber"]
        num = latest["number"]
        res_type = latest["resultType"]
        next_issue = str(safe_int(issue, 0) + 1)

        state.engine.update_history(latest)

        # -------- RESULT CHECK ONLY IF WE PREDICTED THIS ISSUE --------
        if state.active_bet and state.active_bet.predicted_issue == issue:
            if state.last_result_issue == issue:
                await asyncio.sleep(0.15)
                continue

            pick = state.active_bet.pick
            is_win = (pick == res_type)

            # update stats
            if is_win:
                state.wins += 1
                state.streak_win += 1
                state.streak_loss = 0
                state.max_win_streak = max(state.max_win_streak, state.streak_win)
            else:
                state.losses += 1
                state.streak_loss += 1
                state.streak_win = 0
                state.max_loss_streak = max(state.max_loss_streak, state.streak_loss)

            # send stickers (optional)
            if is_win:
                await safe_send_sticker(bot, TARGET_CHAT_ID, STICKERS["WIN"])
            else:
                await safe_send_sticker(bot, TARGET_CHAT_ID, STICKERS["LOSS"])

            # send result message
            await bot.send_message(
                TARGET_CHAT_ID,
                result_text(issue, num, res_type, pick, is_win),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            # delete checking message
            if state.active_bet.checking_msg_id:
                await safe_delete(bot, TARGET_CHAT_ID, state.active_bet.checking_msg_id)

            state.last_result_issue = issue
            state.active_bet = None

            # safety stop at 8 loss step
            if state.streak_loss >= MAX_RECOVERY_STEPS:
                await bot.send_message(
                    TARGET_CHAT_ID,
                    "🧊 <b>SAFETY STOP</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                    "৮ স্টেপ চলে গেছে — সেফটির জন্য সেশন বন্ধ করা হলো ✅",
                    parse_mode=ParseMode.HTML
                )
                # stop without extra signal
                await stop_session(bot)
                break

        # -------- SEND SIGNAL ONLY IF NOT ACTIVE AND NOT DUPLICATED --------
        if (not state.active_bet) and (state.last_signal_issue != next_issue):
            # stop guard
            if not state.running or state.session_id != my_session:
                break

            pick = state.engine.get_pattern_signal(state.streak_loss)
            conf = state.engine.confidence(state.streak_loss)

            # Prediction sticker first (optional)
            await safe_send_sticker(bot, TARGET_CHAT_ID, STICKERS["PRED_BIG"] if pick == "BIG" else STICKERS["PRED_SMALL"])

            # Prediction message
            await bot.send_message(
                TARGET_CHAT_ID,
                signal_text(next_issue, pick, conf),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            # Checking message
            chk = await bot.send_message(
                TARGET_CHAT_ID,
                checking_text(next_issue),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            state.active_bet = ActiveBet(predicted_issue=next_issue, pick=pick, checking_msg_id=chk.message_id)
            state.last_signal_issue = next_issue

        await asyncio.sleep(LOOP_SLEEP_30S if state.mode == "30S" else LOOP_SLEEP_1M)

# =========================
# HANDLERS
# =========================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔒 <b>SYSTEM LOCKED</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Password দিন:",
        parse_mode=ParseMode.HTML
    )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    uid = update.effective_user.id

    if uid not in state.unlocked_users:
        if txt == BOT_PASSWORD:
            state.unlocked_users.add(uid)
            await update.message.reply_text(
                panel_text(),
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu()
            )
        else:
            await update.message.reply_text("❌ <b>WRONG PASSWORD</b>", parse_mode=ParseMode.HTML)
        return

    # already unlocked, show panel
    await update.message.reply_text(
        panel_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu()
    )

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    if uid not in state.unlocked_users:
        await q.edit_message_text("🔒 <b>LOCKED</b>\n/start দিন।", parse_mode=ParseMode.HTML)
        return

    data = q.data or ""

    if data == "REFRESH":
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=main_menu())
        return

    if data.startswith("START:"):
        mode = data.split(":", 1)[1]

        # stop existing session cleanly
        if state.running:
            await stop_session(context.bot)

        await start_session(context.bot, mode)
        my_session = state.session_id
        context.application.create_task(engine_loop(context, my_session))

        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=main_menu())
        return

    if data == "STOP":
        if state.running:
            await stop_session(context.bot)
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=main_menu())
        return

# =========================
# MAIN
# =========================
def main():
    logging.basicConfig(level=logging.WARNING)
    keep_alive()

    app_tg = Application.builder().token(BOT_TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start_cmd))
    app_tg.add_handler(CallbackQueryHandler(cb_handler))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app_tg.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
