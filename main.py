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
# CONFIG (ONLY TOKEN YOU SET)
# =========================
BOT_TOKEN = "8456002611:AAHZUGRB6VEPGwimGwpusCXuUSMS7yL2XTY"

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

# Password source A1
PASSWORD_SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
PASSWORD_SHEET_GID = "0"
PASSWORD_FALLBACK = "2222"

# Settings
MAX_RECOVERY_STEPS = 8
FETCH_TIMEOUT = 6.5

# =========================
# STICKERS
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

    "SUPER_WIN": {
        2: "CAACAgUAAxkBAAEQTiBpcmUfm9aQmlIHtPKiG2nE2e6EeAACcRMAAiLWqFSpdxWmKJ1TXzgE",
        3: "CAACAgUAAxkBAAEQTiFpcmUgdgJQ_czeoFyRhNZiZI2lwwAC8BcAAv8UqFSVBQEdUW48HTgE",
        4: "CAACAgUAAxkBAAEQTiJpcmUgSydN-tKxoSVdFuAvCcJ3fQACvSEAApMRqFQoUYBnH5Pc7TgE",
    },

    "COLOR_RED": "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    "COLOR_GREEN": "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",
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
# HELPERS
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

def pill(text: str) -> str:
    return f"➤ <b>{text}</b>"

def pick_badge(pick: str) -> str:
    return "🟢 <b>BIG</b> 🟢" if pick == "BIG" else "🔴 <b>SMALL</b> 🔴"

def result_badge(res_type: str, number: int) -> str:
    if res_type == "BIG":
        return f"🟢 <b>{number}</b>  •  <b>BIG</b>"
    return f"🔴 <b>{number}</b>  •  <b>SMALL</b>"

# =========================
# PERIOD
# =========================
def calc_period_and_remain(mode: str) -> Tuple[str, int]:
    now = datetime.now(BD_TZ)
    h, m, s = now.hour, now.minute, now.second

    if mode == "30S":
        remain = 30 - (s % 30)
        date_str = now.strftime("%Y%m%d")
        total_minutes = h * 60 + m
        period_index = total_minutes * 2 + (2 if s >= 30 else 1)
        period = f"{date_str}30{period_index:04d}"
        return period, remain
    else:
        remain = 60 - s
        date_str = now.strftime("%Y%m%d")
        total_slots = (h * 60) + m + 1
        period = f"{date_str}01{total_slots:04d}"
        return period, remain

# =========================
# PREDICTION ENGINE
# =========================
class PredictionEngine:
    def __init__(self):
        self.history: List[str] = []
        self.raw_history: List[dict] = []

    def update_history(self, issue_data: dict):
        try:
            number = int(issue_data["number"])
            result_type = "BIG" if number >= 5 else "SMALL"
        except Exception:
            return

        latest_issue = extract_issue_id(issue_data)
        if not latest_issue:
            return

        if (not self.raw_history) or (extract_issue_id(self.raw_history[0]) != latest_issue):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:120]
            self.raw_history = self.raw_history[:120]

    def get_pattern_signal(self, current_streak_loss: int):
        if not self.raw_history:
            return random.choice(["BIG", "SMALL"])
        try:
            last_num = int(self.raw_history[0]["number"])
            pred = "BIG" if (last_num + 1) % 2 == 0 else "SMALL"
            if current_streak_loss >= 2 and self.history:
                pred = self.history[0]
            return pred
        except Exception:
            return random.choice(["BIG", "SMALL"])

    def calc_confidence(self, streak_loss: int) -> int:
        base = random.randint(88, 95)
        if streak_loss >= 1:
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
    max_win_streak: int = 0
    max_loss_streak: int = 0

    unlocked: bool = False
    expected_password: str = PASSWORD_FALLBACK

    selected_targets: List[int] = field(default_factory=lambda: [TARGETS["MAIN_GROUP"]])
    color_mode: bool = False
    graceful_stop_requested: bool = False
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)

    last_api_result: Optional[dict] = None
    last_api_fetch_ts: float = 0.0

state = BotState()

def recovery_text() -> str:
    return f"{state.streak_loss} / {MAX_RECOVERY_STEPS}"

def stats_line() -> str:
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    return f"✅ <b>{state.wins}</b>  |  ❌ <b>{state.losses}</b>  |  🎯 <b>{wr:.1f}%</b>"

def format_signal(issue: str, pick: str, conf: int, remain: int) -> str:
    return (
        f"⚡ <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{pill('MODE')}  <code>{mode_label(state.mode)}</code>\n"
        f"{pill('PERIOD')}  <code>{issue}</code>\n"
        f"{pill('TIMER')}  <b>{remain}s</b> left\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 {pill('PREDICTION')}  {pick_badge(pick)}\n"
        f"🔥 {pill('CONFIDENCE')}  <b>{conf}%</b>\n"
        f"🧠 {pill('RECOVERY')}  <b>{recovery_text()}</b>\n"
        f"⏱ {pill('BD TIME')}  <b>{now_bd_str()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>REGISTER:</b> <a href='{REG_LINK}'>CLICK HERE</a>"
    )

def format_checking(wait_issue: str) -> str:
    return (
        f"🛰 <b>CHECKING RESULT…</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{pill('WAITING')}  <code>{wait_issue}</code>\n"
        f"{pill('MODE')}  <code>{mode_label(state.mode)}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <i>Syncing result from server…</i>"
    )

def format_result(issue: str, number: int, res_type: str, pick: str, is_win: bool) -> str:
    head = "✅ <b>WIN CONFIRMED</b> ✅" if is_win else "❌ <b>LOSS CONFIRMED</b> ❌"
    promo = ""
    if is_win:
        promo = (
            f"\n━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 <b>PREMIUM INFO</b>\n"
            f"👤 <b>Owner:</b> {OWNER_USERNAME}"
        )

    return (
        f"{head}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{pill('PERIOD')}  <code>{issue}</code>\n"
        f"{pill('RESULT')}  {result_badge(res_type, number)}\n"
        f"{pill('YOUR PICK')}  {pick_badge(pick)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 {pill('RECOVERY')}  <b>{recovery_text()}</b>\n"
        f"📊 {pill('STATS')}  {stats_line()}\n"
        f"⏱ {pill('BD TIME')}  <b>{now_bd_str()}</b>"
        f"{promo}"
    )

def format_summary() -> str:
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{pill('MODE')}  <code>{mode_label(state.mode)}</code>\n"
        f"{pill('TOTAL')}  <b>{total}</b>\n"
        f"{pill('WIN')}  <b>{state.wins}</b>\n"
        f"{pill('LOSS')}  <b>{state.losses}</b>\n"
        f"{pill('WIN RATE')}  <b>{wr:.1f}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>JOIN VIP:</b> <a href='{CHANNEL_LINK}'>CLICK HERE</a>"
    )

# =========================
# CONCURRENT BROADCAST
# =========================
async def safe_delete(bot, chat_id: int, msg_id: int):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
        pass

async def broadcast_sticker(bot, sticker_id: str) -> bool:
    tasks = []
    for cid in state.selected_targets:
        tasks.append(bot.send_sticker(cid, sticker_id))
    if not tasks:
        return False
    res = await asyncio.gather(*tasks, return_exceptions=True)
    ok = any(hasattr(r, "message_id") for r in res)
    return ok

async def broadcast_message(bot, text: str) -> Dict[int, int]:
    tasks = []
    cids = []
    for cid in state.selected_targets:
        cids.append(cid)
        tasks.append(
            bot.send_message(
                cid, text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        )
    out: Dict[int, int] = {}
    if tasks:
        res = await asyncio.gather(*tasks, return_exceptions=True)
        for cid, r in zip(cids, res):
            if hasattr(r, "message_id"):
                out[cid] = r.message_id
    return out

# =========================
# API FETCH
# =========================
def _fetch_latest_issue_sync(mode: str) -> Optional[dict]:
    type_id = 5 if mode == "30S" else 1

    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": type_id,
        "language": 0,
        # ✅ dynamic random like browser
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
            if data and "data" in data and "list" in data["data"] and data["data"]["list"]:
                return data["data"]["list"][0]
    except Exception:
        pass
    return None

async def fetch_latest_issue(mode: str) -> Optional[dict]:
    return await asyncio.to_thread(_fetch_latest_issue_sync, mode)

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
        state.active = None

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

    state.last_api_result = None
    state.last_api_fetch_ts = 0.0

    stk = STICKERS["START_30S"] if mode == "30S" else STICKERS["START_1M"]
    await broadcast_sticker(bot, stk)
    await broadcast_sticker(bot, STICKERS["START_END_ALWAYS"])

# =========================
# RESULT PROCESS (ROBUST)
# =========================
async def update_api_cache_and_process(bot, mode: str):
    latest_data = await fetch_latest_issue(mode)
    if not latest_data:
        return

    state.last_api_result = latest_data
    state.last_api_fetch_ts = time.time()

    state.engine.update_history(latest_data)

    latest_issue = extract_issue_id(latest_data)
    if not latest_issue:
        return

    try:
        number = int(latest_data.get("number"))
        latest_type = "BIG" if number >= 5 else "SMALL"
    except Exception:
        return

    if not state.active:
        return

    # ✅ IMPORTANT: strict match only
    if str(state.active.predicted_issue) != str(latest_issue):
        # Debug: console log (deploy log)
        # print(f"[NO MATCH] bet={state.active.predicted_issue} api={latest_issue} mode={mode}")
        return

    pick = state.active.pick
    is_win = (pick == latest_type)

    # --- send stickers (fallback safe) ---
    if is_win:
        state.wins += 1
        state.streak_win += 1
        state.streak_loss = 0
        state.max_win_streak = max(state.max_win_streak, state.streak_win)

        ok = await broadcast_sticker(bot, STICKERS["WIN_ALWAYS"])
        if state.streak_win in STICKERS["SUPER_WIN"]:
            await broadcast_sticker(bot, STICKERS["SUPER_WIN"][state.streak_win])
        else:
            await broadcast_sticker(bot, random.choice(STICKERS["WIN_POOL"]))
        await broadcast_sticker(bot, STICKERS["WIN_BIG"] if latest_type == "BIG" else STICKERS["WIN_SMALL"])
        await broadcast_sticker(bot, STICKERS["WIN_ANY"])

        # ✅ if stickers blocked, still show text
        if not ok:
            await broadcast_message(bot, "✅ <b>WIN</b> (Sticker blocked in this chat)")
    else:
        state.losses += 1
        state.streak_loss += 1
        state.streak_win = 0
        state.max_loss_streak = max(state.max_loss_streak, state.streak_loss)

        ok = await broadcast_sticker(bot, STICKERS["LOSS"])
        if not ok:
            await broadcast_message(bot, "❌ <b>LOSS</b> (Sticker blocked in this chat)")

    # ✅ result message always
    await broadcast_message(bot, format_result(latest_issue, number, latest_type, pick, is_win))

    # cleanup checking
    for cid, mid in (state.active.checking_msg_ids or {}).items():
        await safe_delete(bot, cid, mid)

    state.active = None

    if state.graceful_stop_requested and is_win:
        await stop_session(bot, reason="graceful_done")

# =========================
# ENGINE LOOP (FAST + POLL WHEN ACTIVE)
# =========================
def _issue_diff(a: str, b: str) -> Optional[int]:
    try:
        return int(a) - int(b)
    except Exception:
        return None

async def engine_loop(context: ContextTypes.DEFAULT_TYPE, my_session: int):
    bot = context.bot
    last_signal_issue = None
    last_fetch_ts = 0.0

    while state.running and state.session_id == my_session:
        if state.stop_event.is_set():
            break

        period, remain = calc_period_and_remain(state.mode)

        # Safety stop
        if state.streak_loss >= MAX_RECOVERY_STEPS:
            await broadcast_message(bot, "🧊 <b>SAFETY STOP</b>")
            await stop_session(bot, reason="max_steps")
            break

        # ✅ Keep bet longer (result can be late)
        if state.active:
            diff = _issue_diff(period, state.active.predicted_issue)
            age = time.time() - state.active.created_ts
            # clear only if missed by >=3 periods OR too old
            if (diff is not None and diff >= 3) or age > 160:
                for cid, mid in (state.active.checking_msg_ids or {}).items():
                    await safe_delete(bot, cid, mid)
                state.active = None

        # ✅ API poll schedule
        scheduled = False
        if state.mode == "30S":
            scheduled = remain in (28, 16, 12, 8, 6, 4, 3, 2, 1)
        else:
            scheduled = remain in (55, 30, 20, 12, 8, 5, 3, 2)

        # ✅ If active bet exists, poll more often (critical for win/lose)
        if state.active and (time.time() - last_fetch_ts) > 1.0:
            scheduled = True

        if scheduled:
            last_fetch_ts = time.time()
            context.application.create_task(update_api_cache_and_process(bot, state.mode))

        # ✅ Signal at very start to avoid delay
        if state.mode == "30S":
            signal_window = remain in (30, 29)
        else:
            signal_window = remain in (60, 59, 58)

        if (not state.active) and signal_window and (last_signal_issue != period):
            pred = state.engine.get_pattern_signal(state.streak_loss)
            conf = state.engine.calc_confidence(state.streak_loss)

            s_stk = (
                STICKERS["PRED_30S_BIG"] if pred == "BIG" else STICKERS["PRED_30S_SMALL"]
            ) if state.mode == "30S" else (
                STICKERS["PRED_1M_BIG"] if pred == "BIG" else STICKERS["PRED_1M_SMALL"]
            )

            await broadcast_sticker(bot, s_stk)
            if state.color_mode:
                await broadcast_sticker(bot, STICKERS["COLOR_GREEN"] if pred == "BIG" else STICKERS["COLOR_RED"])

            await broadcast_message(bot, format_signal(period, pred, conf, remain))

            # checking messages
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
            last_signal_issue = period

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
    color = "🎨 <b>COLOR:</b> <b>ON</b>" if state.color_mode else "🎨 <b>COLOR:</b> <b>OFF</b>"
    grace = "🧠 <b>STOP AFTER RECOVER:</b> ✅" if state.graceful_stop_requested else "🧠 <b>STOP AFTER RECOVER:</b> ❌"

    return (
        "🔐 <b>CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Status:</b> {running}\n"
        f"⚡ <b>Mode:</b> <b>{mode_label(state.mode)}</b>\n"
        f"{color}\n"
        f"{grace}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>Send Signals To</b>\n"
        f"{sel_lines}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Live:</b> {stats_line()}\n"
        f"🔥 <b>WinStreak:</b> {state.streak_win} | 🧊 <b>LossStreak:</b> {state.streak_loss}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>Select then Start</i>"
    )

def selector_markup() -> InlineKeyboardMarkup:
    def btn(name: str, chat_id: int) -> InlineKeyboardButton:
        on = "✅" if chat_id in state.selected_targets else "⬜"
        return InlineKeyboardButton(f"{on} {name}", callback_data=f"TOGGLE:{chat_id}")

    rows = [
        [btn("MAIN GROUP", TARGETS["MAIN_GROUP"])],
        [btn("VIP", TARGETS["VIP"]), btn("PUBLIC", TARGETS["PUBLIC"])],
        [InlineKeyboardButton("🎨 Color: ON" if state.color_mode else "🎨 Color: OFF", callback_data="TOGGLE_COLOR")],
        [
            InlineKeyboardButton("⚡ Start 30 SEC", callback_data="START:30S"),
            InlineKeyboardButton("⚡ Start 1 MIN", callback_data="START:1M"),
        ],
        [
            InlineKeyboardButton("🧠 Stop After Recover", callback_data="STOP:GRACEFUL"),
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

    if data == "TOGGLE_COLOR":
        state.color_mode = not state.color_mode
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        return

    if data.startswith("START:"):
        mode = data.split(":")[1]
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

    if data == "STOP:GRACEFUL":
        if state.running:
            state.graceful_stop_requested = True
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
