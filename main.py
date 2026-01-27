import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from threading import Thread
from typing import Dict, List, Optional, Tuple

import requests
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# =========================
# CONFIG (ONLY TOKEN YOU SET)
# =========================
BOT_TOKEN = "PUT_NEW_TOKEN_HERE"  # ✅ অবশ্যই নতুন টোকেন দিন

# --- BRANDING & LINKS ---
BRAND_NAME = "⚡ 𝐓𝐊 𝐌𝐀𝐑𝐔𝐅 𝐕𝐈𝐏 𝐒𝐈𝐆𝐍𝐀𝐋 ⚡"
REG_LINK = "https://tkclub2.com/#/register?invitationCode=18753202056"
OWNER_USERNAME = "@OWNER_MARUF_TOP"
CHANNEL_LINK = "https://t.me/big_maruf_official0"

# Targets
TARGETS = {
    "MAIN_GROUP": -1003263928753,
    "VIP": -1002892329434,
    "PUBLIC": -1002629495753,
}

# API CONFIG
API_URL = "https://api880.inpay88.net/api/webapi/GetNoaverageEmerdList"

# BD Time
BD_TZ = timezone(timedelta(hours=6))

# Password source A1 (Google Sheet)
PASSWORD_SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
PASSWORD_SHEET_GID = "0"
PASSWORD_FALLBACK = "2222"

# Settings
MAX_RECOVERY_STEPS = 8
FETCH_TIMEOUT = 6.0
FETCH_RETRY_SLEEP = 1.0

# =========================
# STICKERS (ONLY 1M)
# =========================
STICKERS = {
    "PRED_1M_BIG": "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    "PRED_1M_SMALL": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",

    "START_1M": "CAACAgUAAxkBAAEQUrRpdYvESSIrn4-Lm936I6F8_BaN-wACChYAAuBHOVc6YQfcV-EKqjgE",
    "START_END_ALWAYS": "CAACAgUAAxkBAAEQTjRpcmWdzXBzA7e9KNz8QgTI6NXlxgACuRcAAh2x-FaJNjq4QG_DujgE",

    "WIN_BIG": "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    "WIN_SMALL": "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    "WIN_ALWAYS": "CAACAgUAAxkBAAEQUTZpdFC4094KaOEdiE3njwhAGVCuBAAC4hoAAt0EqVQXmdKVLGbGmzgE",
    "WIN_ANY": "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA",

    "LOSS": "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",

    "WIN_POOL": [
        "CAACAgUAAxkBAAEQTzNpcz9ns8rx_5xmxk4HHQOJY2uUQQAC3RoAAuCpcFbMKj0VkxPOdTgE",
        "CAACAgUAAxkBAAEQTzRpcz9ni_I4CjwFZ3iSt4xiXxFgkwACkxgAAnQKcVYHd8IiRqfBXTgE",
        "CAACAgUAAxkBAAEQTx9pcz8GryuxGBMFtzRNRbiCTg9M8wAC5xYAAkN_QFWgd5zOh81JGDgE",
    ],
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
# PASSWORD (SHEET A1)
# =========================
def fetch_password_a1() -> str:
    try:
        url = (
            f"https://docs.google.com/spreadsheets/d/{PASSWORD_SHEET_ID}/export"
            f"?format=csv&gid={PASSWORD_SHEET_GID}&range=A1"
        )
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return PASSWORD_FALLBACK
        val = r.text.strip().strip('"').strip()
        return val if val else PASSWORD_FALLBACK
    except Exception:
        return PASSWORD_FALLBACK

async def get_live_password() -> str:
    return await asyncio.to_thread(fetch_password_a1)

# =========================
# PREDICTION ENGINE (1M)
# =========================
class PredictionEngine:
    def __init__(self):
        self.history: List[str] = []
        self.raw_history: List[dict] = []
        self.last_prediction: Optional[str] = None

    def update_history(self, issue_data: dict):
        try:
            number = int(issue_data["number"])
            result_type = "BIG" if number >= 5 else "SMALL"
        except Exception:
            return

        if (not self.raw_history) or (str(self.raw_history[0].get("issueNumber")) != str(issue_data.get("issueNumber"))):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:200]
            self.raw_history = self.raw_history[:200]

    def get_pattern_signal(self, current_streak_loss: int) -> str:
        """
        1) Short history -> random safe
        2) Basic anti-repeat logic using last number parity
        3) If losing streak high -> follow last result (stabilize)
        """
        if not self.raw_history:
            return random.choice(["BIG", "SMALL"])

        try:
            last_num = int(self.raw_history[0]["number"])
            # Slightly smarter: flip when normal, stabilize when losing
            if current_streak_loss >= 2 and self.history:
                prediction = self.history[0]
            else:
                prediction = "BIG" if (last_num % 2 == 0) else "SMALL"

            self.last_prediction = prediction
            return prediction
        except Exception:
            return random.choice(["BIG", "SMALL"])

    def calc_confidence(self, streak_loss: int) -> int:
        base = random.randint(90, 97)
        if streak_loss >= 1:
            base -= 6
        if streak_loss >= 3:
            base -= 6
        return max(65, base)

# =========================
# BOT STATE
# =========================
def now_bd_str() -> str:
    return datetime.now(BD_TZ).strftime("%I:%M:%S %p")

def mode_label() -> str:
    return "1 MIN VIP"

def recovery_label(loss_streak: int) -> str:
    if loss_streak <= 0:
        return f"0 Step / {MAX_RECOVERY_STEPS}"
    return f"{loss_streak} Step Loss / {MAX_RECOVERY_STEPS}"

@dataclass
class ActiveBet:
    predicted_issue: str
    pick: str
    checking_msg_ids: Dict[int, int] = field(default_factory=dict)
    loss_related_ids: Dict[int, List[int]] = field(default_factory=dict)

@dataclass
class BotState:
    running: bool = False
    session_id: int = 0
    engine: PredictionEngine = field(default_factory=PredictionEngine)
    active: Optional[ActiveBet] = None
    last_result_issue: Optional[str] = None
    last_signal_issue: Optional[str] = None

    wins: int = 0
    losses: int = 0
    streak_win: int = 0
    streak_loss: int = 0
    max_win_streak: int = 0
    max_loss_streak: int = 0

    unlocked: bool = False
    expected_password: str = PASSWORD_FALLBACK

    selected_targets: List[int] = field(default_factory=lambda: [TARGETS["MAIN_GROUP"]])
    graceful_stop_requested: bool = False
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)

state = BotState()

# =========================
# FETCH (ONLY 1M typeId=1)
# =========================
def _fetch_latest_issue_sync() -> Optional[dict]:
    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": 1,  # ✅ ONLY 1M
        "language": 0,
        "random": "4ec1d2c67364426aa056214302636756",
        "signature": "D39F9069695C55720235791E0D10D695",
        "timestamp": int(time.time())
    }

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Origin": "https://dkwin9.com",
        "Referer": "https://dkwin9.com/"
    }

    try:
        r = requests.post(API_URL, json=payload, headers=headers, timeout=FETCH_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if data and "data" in data and "list" in data["data"] and data["data"]["list"]:
                return data["data"]["list"][0]
    except Exception as e:
        print(f"API Error: {e}")
    return None

async def fetch_latest_issue() -> Optional[dict]:
    return await asyncio.to_thread(_fetch_latest_issue_sync)

# =========================
# MESSAGES (PREMIUM 1M)
# =========================
def pretty_pick(pick: str) -> str:
    return "🟢🟢 <b>BIG</b> 🟢🟢" if pick == "BIG" else "🔴🔴 <b>SMALL</b> 🔴🔴"

def vip_footer() -> str:
    return (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>OWNER:</b> {OWNER_USERNAME}\n"
        f"📣 <b>VIP CHANNEL:</b> <a href='{CHANNEL_LINK}'>JOIN NOW</a>\n"
        f"📝 <b>REGISTER:</b> <a href='{REG_LINK}'>CREATE ACCOUNT</a>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <i>VIP Signal = Discipline + Money Management</i>"
    )

def format_signal(issue: str, pick: str, conf: int) -> str:
    pick_txt = pretty_pick(pick)
    return (
        f"⚡ <b>{BRAND_NAME}</b>\n"
        f"💎 <b>OFFICIAL 1 MINUTE VIP SIGNAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Mode:</b> <b>{mode_label()}</b>\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>ENTRY:</b> {pick_txt}\n"
        f"📊 <b>Confidence:</b> <b>{conf}%</b>\n"
        f"🧠 <b>Recovery:</b> <b>{recovery_label(state.streak_loss)}</b>\n"
        f"🕒 <b>BD Time:</b> <b>{now_bd_str()}</b>\n"
        + vip_footer()
    )

def format_checking(wait_issue: str) -> str:
    return (
        "🛰 <b>RESULT CHECKING...</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Waiting Period:</b> <code>{wait_issue}</code>\n"
        f"🕒 <b>BD Time:</b> <b>{now_bd_str()}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ <i>Server sync in progress...</i>"
    )

def format_result(issue: str, res_num: str, res_type: str, pick: str, is_win: bool) -> str:
    pick_txt = pretty_pick(pick)
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if is_win:
        header = "✅ <b>WIN CONFIRMED</b> ✅"
        promo = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 <b>VIP ACCESS BENEFITS</b>\n"
            "✅ Daily Premium Signals\n"
            "✅ Strong Recovery System\n"
            "✅ High Quality Support\n"
            f"📩 <b>Inbox:</b> {OWNER_USERNAME}\n"
        )
    else:
        header = "❌ <b>LOSS CONFIRMED</b> ❌"
        promo = ""

    return (
        f"{header}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{res_num} ({res_type})</b>\n"
        f"🎯 <b>Your Pick:</b> {pick_txt}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 <b>Recovery:</b> <b>{recovery_label(state.streak_loss)}</b>\n"
        f"📊 <b>W:</b> <b>{state.wins}</b> | <b>L:</b> <b>{state.losses}</b>\n"
        f"🕒 <b>BD Time:</b> <b>{now_bd_str()}</b>\n"
        f"{promo}"
        + vip_footer()
    ).strip()

def format_summary() -> str:
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    return (
        "🛑 <b>SESSION CLOSED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Mode:</b> <b>{mode_label()}</b>\n"
        f"📦 <b>Total:</b> <b>{total}</b>\n"
        f"✅ <b>Win:</b> <b>{state.wins}</b>\n"
        f"❌ <b>Loss:</b> <b>{state.losses}</b>\n"
        f"🎯 <b>Win Rate:</b> <b>{wr:.1f}%</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>Max Win Streak:</b> <b>{state.max_win_streak}</b>\n"
        f"🧨 <b>Max Loss Streak:</b> <b>{state.max_loss_streak}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 <b>Closed:</b> <b>{now_bd_str()}</b>\n"
        + vip_footer()
    )

# =========================
# PANEL
# =========================
def _chat_name(chat_id: int) -> str:
    if chat_id == TARGETS["MAIN_GROUP"]: return "MAIN GROUP"
    if chat_id == TARGETS["VIP"]: return "VIP"
    if chat_id == TARGETS["PUBLIC"]: return "PUBLIC"
    return str(chat_id)

def panel_text() -> str:
    running = "🟢 RUNNING" if state.running else "🔴 STOPPED"
    sel = state.selected_targets[:] if state.selected_targets else [TARGETS["MAIN_GROUP"]]
    sel_lines = "\n".join([f"✅ <b>{_chat_name(cid)}</b> <code>{cid}</code>" for cid in sel])
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0

    return (
        "🔐 <b>CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Status:</b> {running}\n"
        f"⚡ <b>Mode:</b> <b>{mode_label()}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>Send Signals To</b>\n"
        f"{sel_lines}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>Live Stats</b>\n"
        f"✅ Win: <b>{state.wins}</b>\n"
        f"❌ Loss: <b>{state.losses}</b>\n"
        f"🎯 WinRate: <b>{wr:.1f}%</b>\n"
        f"🔥 WinStreak: <b>{state.streak_win}</b> | 🧊 LossStreak: <b>{state.streak_loss}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>Select then Start</i>"
    )

def selector_markup() -> InlineKeyboardMarkup:
    def btn(name: str, chat_id: int) -> InlineKeyboardButton:
        on = "✅" if chat_id in state.selected_targets else "⬜"
        return InlineKeyboardButton(f"{on} {name}", callback_data=f"TOGGLE:{chat_id}")

    rows = [
        [btn("MAIN GROUP", TARGETS["MAIN_GROUP"])],
        [btn("VIP", TARGETS["VIP"]), btn("PUBLIC", TARGETS["PUBLIC"])],
        [
            InlineKeyboardButton("⚡ Start 1 MIN VIP", callback_data="START:1M"),
        ],
        [
            InlineKeyboardButton("🧠 Stop After Win", callback_data="STOP:GRACEFUL"),
            InlineKeyboardButton("🛑 Stop Now", callback_data="STOP:FORCE"),
        ],
        [InlineKeyboardButton("🔄 Refresh Panel", callback_data="REFRESH_PANEL")]
    ]
    return InlineKeyboardMarkup(rows)

# =========================
# HELPERS
# =========================
async def safe_delete(bot, chat_id: int, msg_id: int):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
        pass

async def broadcast_sticker(bot, sticker_id: str):
    for cid in state.selected_targets:
        try:
            await bot.send_sticker(cid, sticker_id)
        except Exception:
            pass

async def broadcast_message(bot, text: str) -> Dict[int, int]:
    out = {}
    for cid in state.selected_targets:
        try:
            m = await bot.send_message(
                cid,
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            out[cid] = m.message_id
        except Exception:
            pass
    return out

# =========================
# SESSION CONTROL
# =========================
def reset_stats():
    state.wins = 0
    state.losses = 0
    state.streak_win = 0
    state.streak_loss = 0
    state.max_win_streak = 0
    state.max_loss_streak = 0

async def stop_session(bot, reason: str = "manual"):
    state.session_id += 1
    state.running = False
    state.stop_event.set()

    if state.active:
        for cid, mid in (state.active.checking_msg_ids or {}).items():
            await safe_delete(bot, cid, mid)
        for cid, mids in (state.active.loss_related_ids or {}).items():
            for mid in mids:
                await safe_delete(bot, cid, mid)

    await broadcast_sticker(bot, STICKERS["START_END_ALWAYS"])

    for cid in state.selected_targets:
        try:
            await bot.send_message(
                cid,
                format_summary(),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception:
            pass

    state.unlocked = False
    state.active = None
    state.graceful_stop_requested = False

async def start_session(bot):
    state.session_id += 1
    state.running = True
    state.stop_event.clear()
    state.graceful_stop_requested = False
    state.engine = PredictionEngine()
    state.active = None
    state.last_result_issue = None
    state.last_signal_issue = None
    reset_stats()

    await broadcast_sticker(bot, STICKERS["START_1M"])
    await broadcast_sticker(bot, STICKERS["START_END_ALWAYS"])

# =========================
# ENGINE LOOP (ONLY 1M, SMART TIMING)
# =========================
def calc_current_1m_period(now: datetime) -> str:
    date_str = now.strftime("%Y%m%d")
    total_slots = (now.hour * 60) + now.minute + 1
    return f"{date_str}01{total_slots:04d}"

async def engine_loop(context: ContextTypes.DEFAULT_TYPE, my_session: int):
    bot = context.bot

    # Small anti-spam: keep last sent time
    while state.running and state.session_id == my_session:
        if state.stop_event.is_set():
            break

        now = datetime.now(BD_TZ)
        sec = now.second

        current_running_period = calc_current_1m_period(now)

        # ✅ Safe window: 05-40 sec (avoid last seconds delay)
        is_safe_time = (5 <= sec <= 40)

        # 1) Fetch latest closed result
        latest_data = await fetch_latest_issue()
        if latest_data:
            state.engine.update_history(latest_data)

            latest_issue = str(latest_data.get("issueNumber"))
            latest_type = "BIG" if int(latest_data.get("number")) >= 5 else "SMALL"

            # If we have an active bet, check result
            if state.active:
                if state.active.predicted_issue == latest_issue:
                    pick = state.active.pick
                    is_win = (pick == latest_type)

                    if is_win:
                        state.wins += 1
                        state.streak_win += 1
                        state.streak_loss = 0
                        state.max_win_streak = max(state.max_win_streak, state.streak_win)

                        await broadcast_sticker(bot, STICKERS["WIN_ALWAYS"])
                        await broadcast_sticker(bot, random.choice(STICKERS["WIN_POOL"]))
                        await broadcast_sticker(bot, STICKERS["WIN_BIG"] if latest_type == "BIG" else STICKERS["WIN_SMALL"])
                        await broadcast_sticker(bot, STICKERS["WIN_ANY"])
                    else:
                        state.losses += 1
                        state.streak_loss += 1
                        state.streak_win = 0
                        state.max_loss_streak = max(state.max_loss_streak, state.streak_loss)
                        await broadcast_sticker(bot, STICKERS["LOSS"])

                    await broadcast_message(
                        bot,
                        format_result(latest_issue, str(latest_data.get("number")), latest_type, pick, is_win)
                    )

                    # cleanup checking messages
                    for cid, mid in (state.active.checking_msg_ids or {}).items():
                        await safe_delete(bot, cid, mid)

                    state.active = None

                    # graceful stop only after a WIN
                    if state.graceful_stop_requested and is_win:
                        await stop_session(bot, reason="graceful_done")
                        break

                # If API jumped past our predicted issue, skip (missed)
                elif latest_issue.isdigit() and state.active.predicted_issue.isdigit():
                    if int(latest_issue) > int(state.active.predicted_issue):
                        for cid, mid in (state.active.checking_msg_ids or {}).items():
                            await safe_delete(bot, cid, mid)
                        state.active = None

        # 2) Signal generation
        if (not state.active) and is_safe_time:
            if state.last_signal_issue != current_running_period:

                if state.streak_loss >= MAX_RECOVERY_STEPS:
                    await broadcast_message(bot, "🧊 <b>SAFETY STOP</b>\n<i>Max recovery steps reached.</i>")
                    await stop_session(bot, reason="max_steps")
                    break

                pred = state.engine.get_pattern_signal(state.streak_loss)
                conf = state.engine.calc_confidence(state.streak_loss)

                s_stk = STICKERS["PRED_1M_BIG"] if pred == "BIG" else STICKERS["PRED_1M_SMALL"]
                await broadcast_sticker(bot, s_stk)

                await broadcast_message(bot, format_signal(current_running_period, pred, conf))

                # checking message
                checking_ids = {}
                for cid in state.selected_targets:
                    try:
                        m = await bot.send_message(cid, format_checking(current_running_period), parse_mode=ParseMode.HTML)
                        checking_ids[cid] = m.message_id
                    except Exception:
                        pass

                bet = ActiveBet(predicted_issue=current_running_period, pick=pred)
                bet.checking_msg_ids = checking_ids
                for cid, mid in checking_ids.items():
                    bet.loss_related_ids.setdefault(cid, []).append(mid)

                state.active = bet
                state.last_signal_issue = current_running_period

        await asyncio.sleep(0.6)

# =========================
# COMMANDS & CALLBACKS
# =========================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.expected_password = await get_live_password()
    state.unlocked = False
    await update.message.reply_text(
        "🔒 <b>SYSTEM LOCKED</b>\n✅ Password দিন:",
        parse_mode=ParseMode.HTML
    )

async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state.unlocked:
        state.expected_password = await get_live_password()
        await update.message.reply_text("🔒 <b>LOCKED</b>", parse_mode=ParseMode.HTML)
        return
    await update.message.reply_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if not state.unlocked:
        state.expected_password = await get_live_password()
        if txt == state.expected_password:
            state.unlocked = True
            await update.message.reply_text("✅ <b>UNLOCKED</b>", parse_mode=ParseMode.HTML)
            await update.message.reply_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        else:
            await update.message.reply_text("❌ <b>WRONG PASSWORD</b>", parse_mode=ParseMode.HTML)
        return

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""

    if not state.unlocked:
        await q.edit_message_text("🔒 <b>LOCKED</b>")
        return

    if data == "REFRESH_PANEL":
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        return

    if data.startswith("TOGGLE:"):
        cid = int(data.split(":")[1])
        if cid in state.selected_targets:
            state.selected_targets.remove(cid)
        else:
            state.selected_targets.append(cid)
        if not state.selected_targets:
            state.selected_targets = [TARGETS["MAIN_GROUP"]]
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        return

    if data == "START:1M":
        if state.running:
            await stop_session(context.bot, reason="restart")
        await start_session(context.bot)
        context.application.create_task(engine_loop(context, state.session_id))
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        return

    if data == "STOP:FORCE":
        if state.running:
            await stop_session(context.bot, reason="force")
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        return

    if data == "STOP:GRACEFUL":
        if state.running:
            state.graceful_stop_requested = True
            # if no active bet and no loss streak, stop now
            if state.streak_loss == 0 and state.active is None:
                await stop_session(context.bot, reason="graceful_now")
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        return

# =========================
# MAIN
# =========================
def main():
    logging.basicConfig(level=logging.WARNING)
    keep_alive()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("panel", cmd_panel))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
