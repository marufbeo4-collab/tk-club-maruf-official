import asyncio
import logging
import os
import random
import time
import secrets
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
# CONFIG
# =========================
BOT_TOKEN = "8456002611:AAHZUGRB6VEPGwimGwpusCXuUSMS7yL2XTY"

BRAND_NAME = "⚡ 𝐓𝐊 𝐌𝐀𝐑𝐔𝐅 𝐕𝐈𝐏 𝐒𝐈𝐆𝐍𝐀𝐋 ⚡"
REG_LINK = "https://tkclub2.com/#/register?invitationCode=18753202056"
OWNER_USERNAME = "@OWNER_MARUF_TOP"
CHANNEL_LINK = "https://t.me/big_maruf_official0"

TARGETS = {
    "MAIN_GROUP": -1003263928753,
    "VIP": -1002892329434,
    "PUBLIC": -1002629495753,
}

API_URL = "https://api880.inpay88.net/api/webapi/GetNoaverageEmerdList"
BD_TZ = timezone(timedelta(hours=6))

PASSWORD_SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
PASSWORD_SHEET_GID = "0"
PASSWORD_FALLBACK = "2222"

MAX_RECOVERY_STEPS = 8
FETCH_TIMEOUT = 6.5

# =========================
# STICKERS (same as yours)
# =========================
STICKERS = {
    "PRED_1M_BIG": "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    "PRED_1M_SMALL": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",
    "PRED_30S_BIG": "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",
    "PRED_30S_SMALL": "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",

    "START_30S": "CAACAgUAAxkBAAEQUrNpdYvDXIBff9O8TCRlI3QYJgfGiAAC1RQAAjGFMVfjtqxbDWbuEzgE",
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
    Thread(target=run_http, daemon=True).start()

# =========================
# PASSWORD
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
# UTILS
# =========================
def now_bd_str() -> str:
    return datetime.now(BD_TZ).strftime("%H:%M:%S")

def mode_label(mode: str) -> str:
    return "30 SEC" if mode == "30S" else "1 MIN"

def extract_issue_id(d: dict) -> Optional[str]:
    for k in ("issueNumber", "issueNo", "issueId", "issue", "period"):
        v = d.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None

def calc_period_and_remain(mode: str) -> Tuple[str, int]:
    now = datetime.now(BD_TZ)
    h, m, s = now.hour, now.minute, now.second

    if mode == "30S":
        remain = 30 - (s % 30)
        date_str = now.strftime("%Y%m%d")
        total_minutes = h * 60 + m
        idx = total_minutes * 2 + (2 if s >= 30 else 1)
        period = f"{date_str}30{idx:04d}"
        return period, remain
    else:
        remain = 60 - s
        date_str = now.strftime("%Y%m%d")
        idx = (h * 60) + m + 1
        period = f"{date_str}01{idx:04d}"
        return period, remain

# =========================
# PREDICTION ENGINE
# =========================
class PredictionEngine:
    def __init__(self):
        self.raw_history: List[dict] = []
        self.history: List[str] = []

    def update_history(self, d: dict):
        try:
            num = int(d["number"])
            t = "BIG" if num >= 5 else "SMALL"
        except Exception:
            return
        issue = extract_issue_id(d)
        if not issue:
            return
        if not self.raw_history or extract_issue_id(self.raw_history[0]) != issue:
            self.raw_history.insert(0, d)
            self.history.insert(0, t)
            self.raw_history = self.raw_history[:120]
            self.history = self.history[:120]

    def predict(self, loss_streak: int) -> str:
        if not self.raw_history:
            return random.choice(["BIG", "SMALL"])
        try:
            last_num = int(self.raw_history[0]["number"])
            pred = "BIG" if (last_num + 1) % 2 == 0 else "SMALL"
            if loss_streak >= 2 and self.history:
                pred = self.history[0]
            return pred
        except Exception:
            return random.choice(["BIG", "SMALL"])

    def confidence(self, loss_streak: int) -> int:
        base = random.randint(88, 95)
        if loss_streak >= 1:
            base -= 5
        return max(50, min(99, base))

# =========================
# STATE
# =========================
@dataclass
class ActiveBet:
    predicted_issue: str
    pick: str
    created_ts: float = field(default_factory=lambda: time.time())
    checking_msg_ids: Dict[int, int] = field(default_factory=dict)

@dataclass
class BotState:
    running: bool = False
    mode: str = "30S"
    session_id: int = 0

    engine: PredictionEngine = field(default_factory=PredictionEngine)
    active: Optional[ActiveBet] = None

    wins: int = 0
    losses: int = 0
    streak_win: int = 0
    streak_loss: int = 0

    unlocked: bool = False
    expected_password: str = PASSWORD_FALLBACK

    selected_targets: List[int] = field(default_factory=lambda: [TARGETS["MAIN_GROUP"]])
    color_mode: bool = False
    graceful_stop_requested: bool = False
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)

    # ✅ anti-duplicate
    last_signal_issue: Optional[str] = None
    last_result_issue: Optional[str] = None

    # ✅ locks / fetch control
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    api_in_flight: bool = False
    last_api_fetch_ts: float = 0.0

state = BotState()

# =========================
# MESSAGES (simple premium, you can tweak)
# =========================
def format_signal(issue: str, pick: str, conf: int, remain: int) -> str:
    return (
        f"<b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"⏳ <b>Timer:</b> <b>{remain}s</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>PREDICTION</b> ➜ {'🟢🟢 <b>BIG</b> 🟢🟢' if pick=='BIG' else '🔴🔴 <b>SMALL</b> 🔴🔴'}\n"
        f"🔥 <b>Confidence</b> ➜ <b>{conf}%</b>\n"
        f"🧠 <b>Recovery</b> ➜ <b>{state.streak_loss} / {MAX_RECOVERY_STEPS}</b>\n"
        f"⏱ <b>BD Time</b> ➜ <b>{now_bd_str()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>REGISTER:</b> <a href='{REG_LINK}'>CLICK HERE</a>"
    )

def format_checking(issue: str) -> str:
    return (
        f"🛰 <b>CHECKING RESULT...</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"🧾 <b>Waiting:</b> <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <i>Syncing result from server...</i>"
    )

def format_result(issue: str, number: int, res_type: str, pick: str, is_win: bool) -> str:
    head = "✅ <b>WIN CONFIRMED</b> ✅" if is_win else "❌ <b>LOSS CONFIRMED</b> ❌"
    return (
        f"{head}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> <b>{number} ({res_type})</b>\n"
        f"🎯 <b>Your Pick:</b> <b>{pick}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>Win:</b> {state.wins} | ❌ <b>Loss:</b> {state.losses}\n"
        f"⏱ <b>BD Time:</b> <b>{now_bd_str()}</b>"
    )

def format_summary() -> str:
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"📦 <b>Total:</b> <b>{total}</b>\n"
        f"✅ <b>Win:</b> <b>{state.wins}</b>\n"
        f"❌ <b>Loss:</b> <b>{state.losses}</b>\n"
        f"🎯 <b>Win Rate:</b> <b>{wr:.1f}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>JOIN VIP:</b> <a href='{CHANNEL_LINK}'>CLICK HERE</a>"
    )

# =========================
# SEND HELPERS (concurrent but ordered in engine)
# =========================
async def safe_delete(bot, chat_id: int, msg_id: int):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
        pass

async def broadcast_sticker(bot, sticker_id: str):
    tasks = [bot.send_sticker(cid, sticker_id) for cid in state.selected_targets]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

async def broadcast_message(bot, text: str) -> Dict[int, int]:
    tasks = []
    cids = []
    for cid in state.selected_targets:
        cids.append(cid)
        tasks.append(bot.send_message(cid, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True))
    out: Dict[int, int] = {}
    if tasks:
        res = await asyncio.gather(*tasks, return_exceptions=True)
        for cid, r in zip(cids, res):
            if hasattr(r, "message_id"):
                out[cid] = r.message_id
    return out

# =========================
# API FETCH (single in-flight)
# =========================
def _fetch_latest_issue_sync(mode: str) -> Optional[dict]:
    type_id = 5 if mode == "30S" else 1
    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": type_id,
        "language": 0,
        "random": secrets.token_hex(16),
        "signature": "D39F9069695C55720235791E0D10D695",
        "timestamp": int(time.time()),
    }
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://dkwin9.com",
        "Referer": "https://dkwin9.com/",
    }
    try:
        r = requests.post(API_URL, json=payload, headers=headers, timeout=FETCH_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if data and data.get("data") and data["data"].get("list"):
                return data["data"]["list"][0]
    except Exception:
        pass
    return None

async def fetch_latest_issue(mode: str) -> Optional[dict]:
    return await asyncio.to_thread(_fetch_latest_issue_sync, mode)

# =========================
# SESSION
# =========================
def reset_stats():
    state.wins = 0
    state.losses = 0
    state.streak_win = 0
    state.streak_loss = 0
    state.last_signal_issue = None
    state.last_result_issue = None

async def stop_session(bot, reason: str = "manual"):
    state.session_id += 1
    state.running = False
    state.stop_event.set()

    # delete checking if exists
    if state.active:
        for cid, mid in (state.active.checking_msg_ids or {}).items():
            await safe_delete(bot, cid, mid)
        state.active = None

    await broadcast_sticker(bot, STICKERS["START_END_ALWAYS"])
    for cid in state.selected_targets:
        try:
            await bot.send_message(cid, format_summary(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except Exception:
            pass

    state.unlocked = False
    state.graceful_stop_requested = False

async def start_session(bot, mode: str):
    state.mode = mode
    state.session_id += 1
    state.running = True
    state.stop_event.clear()
    state.graceful_stop_requested = False
    state.engine = PredictionEngine()
    state.active = None
    reset_stats()

    stk = STICKERS["START_30S"] if mode == "30S" else STICKERS["START_1M"]
    await broadcast_sticker(bot, stk)
    await broadcast_sticker(bot, STICKERS["START_END_ALWAYS"])

# =========================
# RESULT PROCESS (LOCKED)
# =========================
async def api_fetch_and_process(bot, mode: str):
    # ✅ in-flight guard
    async with state.lock:
        if state.api_in_flight:
            return
        # rate limit (avoid spam)
        if time.time() - state.last_api_fetch_ts < 0.8:
            return
        state.api_in_flight = True
        state.last_api_fetch_ts = time.time()

    try:
        d = await fetch_latest_issue(mode)
        if not d:
            return

        state.engine.update_history(d)
        issue = extract_issue_id(d)
        if not issue:
            return

        try:
            number = int(d.get("number"))
            res_type = "BIG" if number >= 5 else "SMALL"
        except Exception:
            return

        # ✅ lock around active compare + send (prevents double result)
        async with state.lock:
            if not state.active:
                return
            if state.active.predicted_issue != issue:
                return
            if state.last_result_issue == issue:
                return

            pick = state.active.pick
            is_win = (pick == res_type)

            # update stats
            if is_win:
                state.wins += 1
                state.streak_win += 1
                state.streak_loss = 0
            else:
                state.losses += 1
                state.streak_loss += 1
                state.streak_win = 0

            # ✅ required order:
            # 1) win/lose sticker
            await broadcast_sticker(bot, random.choice(STICKERS["WIN_POOL"]) if is_win else STICKERS["LOSS"])
            if is_win:
                await broadcast_sticker(bot, STICKERS["WIN_ALWAYS"])
                await broadcast_sticker(bot, STICKERS["WIN_BIG"] if res_type == "BIG" else STICKERS["WIN_SMALL"])
                await broadcast_sticker(bot, STICKERS["WIN_ANY"])

            # 2) result message
            await broadcast_message(bot, format_result(issue, number, res_type, pick, is_win))

            # 3) delete checking
            for cid, mid in (state.active.checking_msg_ids or {}).items():
                await safe_delete(bot, cid, mid)

            state.last_result_issue = issue
            state.active = None
    finally:
        async with state.lock:
            state.api_in_flight = False

# =========================
# ENGINE LOOP (STRICT ORDER)
# =========================
async def engine_loop(context: ContextTypes.DEFAULT_TYPE, my_session: int):
    bot = context.bot

    while state.running and state.session_id == my_session:
        if state.stop_event.is_set():
            break

        period, remain = calc_period_and_remain(state.mode)

        # Safety stop
        if state.streak_loss >= MAX_RECOVERY_STEPS:
            await broadcast_message(bot, "🧊 <b>SAFETY STOP</b>")
            await stop_session(bot, reason="max_steps")
            break

        # ✅ SIGNAL ONLY ONCE per period (LOCKED)
        # trigger at start only
        signal_window = (remain in (30, 29)) if state.mode == "30S" else (remain in (60, 59))

        if signal_window:
            async with state.lock:
                can_send = (state.active is None) and (state.last_signal_issue != period)
                if can_send:
                    pred = state.engine.predict(state.streak_loss)
                    conf = state.engine.confidence(state.streak_loss)

                    # 1) prediction sticker
                    stk = (STICKERS["PRED_30S_BIG"] if pred == "BIG" else STICKERS["PRED_30S_SMALL"]) if state.mode == "30S" else \
                          (STICKERS["PRED_1M_BIG"] if pred == "BIG" else STICKERS["PRED_1M_SMALL"])
                    await broadcast_sticker(bot, stk)

                    # 2) prediction message
                    await broadcast_message(bot, format_signal(period, pred, conf, remain))

                    # 3) checking message
                    checking_ids: Dict[int, int] = {}
                    tasks = []
                    cids = []
                    for cid in state.selected_targets:
                        cids.append(cid)
                        tasks.append(bot.send_message(cid, format_checking(period), parse_mode=ParseMode.HTML))
                    res = await asyncio.gather(*tasks, return_exceptions=True)
                    for cid, r in zip(cids, res):
                        if hasattr(r, "message_id"):
                            checking_ids[cid] = r.message_id

                    state.active = ActiveBet(predicted_issue=period, pick=pred, checking_msg_ids=checking_ids)
                    state.last_signal_issue = period

        # ✅ API polling:
        # - normal schedule
        # - if active bet exists, poll faster
        poll = False
        if state.mode == "30S":
            poll = remain in (28, 16, 10, 6, 4, 3, 2, 1)
        else:
            poll = remain in (55, 30, 15, 10, 6, 4, 2)

        if state.active and (time.time() - state.last_api_fetch_ts) > 0.9:
            poll = True

        if poll:
            context.application.create_task(api_fetch_and_process(bot, state.mode))

        await asyncio.sleep(0.12)

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
    return (
        "🔐 <b>CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Status:</b> {running}\n"
        f"⚡ <b>Mode:</b> <b>{mode_label(state.mode)}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>Send Signals To</b>\n"
        f"{sel_lines}\n"
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
            InlineKeyboardButton("⚡ Start 30 SEC", callback_data="START:30S"),
            InlineKeyboardButton("⚡ Start 1 MIN", callback_data="START:1M"),
        ],
        [
            InlineKeyboardButton("🛑 Stop Now", callback_data="STOP:FORCE"),
        ],
        [InlineKeyboardButton("🔄 Refresh Panel", callback_data="REFRESH_PANEL")]
    ]
    return InlineKeyboardMarkup(rows)

# =========================
# COMMANDS & CALLBACKS
# =========================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.expected_password = await get_live_password()
    state.unlocked = False
    await update.message.reply_text("🔒 <b>SYSTEM LOCKED</b>\n✅ Password দিন:", parse_mode=ParseMode.HTML)

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

    if data.startswith("START:"):
        mode = data.split(":")[1]

        # ✅ stop previous loop strictly
        if state.running:
            await stop_session(context.bot, reason="restart")

        await start_session(context.bot, mode)
        context.application.create_task(engine_loop(context, state.session_id))
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        return

    if data == "STOP:FORCE":
        if state.running:
            await stop_session(context.bot, reason="force")
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
