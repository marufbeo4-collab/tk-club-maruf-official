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
# CONFIG (REPLACE THESE)
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8456002611:AAHZUGRB6VEPGwimGwpusCXuUSMS7yL2XTY")  # ✅ paste here (or set Render env BOT_TOKEN)

BRAND_NAME = "⚡ TK MARUF OFFICIAL 24/7 SIGNAL"
CHANNEL_LINK = "https://t.me/big_maruf_official0"

# Targets (single)
TARGETS = {
    "MAIN_GROUP": -1003263928753,
}

# =========================
# NEW API (CHANGED)
# =========================
WIN_GO_API = "https://api880.inpay88.net/api/webapi/GetNoaverageEmerdList"
TYPEID_30S = 5
TYPEID_1M = 1

# =========================
# BD Time
# =========================
BD_TZ = timezone(timedelta(hours=6))

# =========================
# PASSWORD (A1 CSV EXPORT - STABLE)
# =========================
PASSWORD_SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
PASSWORD_SHEET_GID = "0"
PASSWORD_FALLBACK = "2222"

# =========================
# Settings
# =========================
MAX_RECOVERY_STEPS = 8
FAST_LOOP_30S = 0.85
FAST_LOOP_1M = 1.65
FETCH_TIMEOUT = 8.0
FETCH_RETRY_SLEEP = 0.50


# =========================
# STICKERS (SAME AS BEFORE)
# =========================
STICKERS = {
    # Prediction (1M)
    "PRED_1M_BIG": "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    "PRED_1M_SMALL": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",

    # Prediction (30S) — swapped as you requested
    "PRED_30S_BIG": "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",
    "PRED_30S_SMALL": "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",

    # Start stickers per mode
    "START_30S": "CAACAgUAAxkBAAEQUrNpdYvDXIBff9O8TCRlI3QYJgfGiAAC1RQAAjGFMVfjtqxbDWbuEzgE",
    "START_1M": "CAACAgUAAxkBAAEQUrRpdYvESSIrn4-Lm936I6F8_BaN-wACChYAAuBHOVc6YQfcV-EKqjgE",

    # Always give this at START/END (but NOT on loss)
    "START_END_ALWAYS": "CAACAgUAAxkBAAEQTjRpcmWdzXBzA7e9KNz8QgTI6NXlxgACuRcAAh2x-FaJNjq4QG_DujgE",

    # Win stickers
    "WIN_BIG": "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    "WIN_SMALL": "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",

    # Every win sticker (required)
    "WIN_ALWAYS": "CAACAgUAAxkBAAEQUTZpdFC4094KaOEdiE3njwhAGVCuBAAC4hoAAt0EqVQXmdKVLGbGmzgE",

    # Any win extra sticker
    "WIN_ANY": "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA",

    # Loss sticker
    "LOSS": "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",

    # Random win pool
    "WIN_POOL": [
        "CAACAgUAAxkBAAEQTzNpcz9ns8rx_5xmxk4HHQOJY2uUQQAC3RoAAuCpcFbMKj0VkxPOdTgE",
        "CAACAgUAAxkBAAEQTzRpcz9ni_I4CjwFZ3iSt4xiXxFgkwACkxgAAnQKcVYHd8IiRqfBXTgE",
        "CAACAgUAAxkBAAEQTx9pcz8GryuxGBMFtzRNRbiCTg9M8wAC5xYAAkN_QFWgd5zOh81JGDgE",
        "CAACAgUAAxkBAAEQT_tpc4E3AxHmgW9VWKrzWjxlrvzSowACghkAAlbXcFWxdto6TqiBrzgE",
        "CAACAgUAAxkBAAEQT_9pc4FHKn0W6ZfWOSaN6FUPzfmbnQACXR0AAqMbMFc-_4DHWbq7sjgE",
        "CAACAgUAAxkBAAEQUAFpc4FIokHE09p165cCsWiUYV648wACuhQAAo3aMVeAsNW9VRuVvzgE",
        "CAACAgUAAxkBAAEQUANpc4FJNTnfuBiLe-dVtoNCf3CQlAAC9xcAArE-MFfS5HNyds2tWTgE",
        "CAACAgUAAxkBAAEQUAVpc4FKhJ_stZ3VRRzWUuJGaWbrAgACOhYAAst6OVehdeQEGZlXiDgE",
        "CAACAgUAAxkBAAEQUAtpc4HcYxkscyRY2rhAAcmqMR29eAACOBYAAh7fwVU5Xy399k3oFDgE",
        "CAACAgUAAxkBAAEQUCdpc4IuoaqPZ-5vn2RTlJZ_kbeXHQACXRUAAgln-FQ8iTzzJg_GLzgE",
    ],

    # Super win streak 2..10 (required)
    "SUPER_WIN": {
        2: "CAACAgUAAxkBAAEQTiBpcmUfm9aQmlIHtPKiG2nE2e6EeAACcRMAAiLWqFSpdxWmKJ1TXzgE",
        3: "CAACAgUAAxkBAAEQTiFpcmUgdgJQ_czeoFyRhNZiZI2lwwAC8BcAAv8UqFSVBQEdUW48HTgE",
        4: "CAACAgUAAxkBAAEQTiJpcmUgSydN-tKxoSVdFuAvCcJ3fQACvSEAApMRqFQoUYBnH5Pc7TgE",
        5: "CAACAgUAAxkBAAEQTiNpcmUgu_dP3wKT2k94EJCiw3u52QACihoAArkfqFSlrldtXbLGGDgE",
        6: "CAACAgUAAxkBAAEQTiRpcmUhQJUjd2ukdtfEtBjwtMH4MAACWRgAAsTFqVTato0SmSN-6jgE",
        7: "CAACAgUAAxkBAAEQTiVpcmUhha9HAAF19fboYayfUrm3tdYAAioXAAIHgKhUD0QmGyF5Aug4BA",
        8: "CAACAgUAAxkBAAEQTixpcmUmevnNEqUbr0qbbVgW4psMNQACMxUAAow-qFSnSz4Ik1ddNzgE",
        9: "CAACAgUAAxkBAAEQTi1pcmUmpSxAHo2pvR-GjCPTmkLr0AACLh0AAhCRqFRH5-2YyZKq1jgE",
        10:"CAACAgUAAxkBAAEQTi5pcmUmjmjp7oXg4InxI1dGYruxDwACqBgAAh19qVT6X_-oEywCkzgE",
    },

    # Color stickers
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
# PASSWORD (A1 CSV EXPORT - STABLE)
# =========================
def fetch_password_a1() -> str:
    try:
        url = (
            f"https://docs.google.com/spreadsheets/d/{PASSWORD_SHEET_ID}/export"
            f"?format=csv&gid={PASSWORD_SHEET_GID}&range=A1"
        )
        r = requests.get(
            url,
            timeout=8,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        if r.status_code != 200:
            return PASSWORD_FALLBACK
        val = r.text.strip().strip('"').strip()
        return val if val else PASSWORD_FALLBACK
    except Exception:
        return PASSWORD_FALLBACK

async def get_live_password() -> str:
    return await asyncio.to_thread(fetch_password_a1)


# =========================
# PREDICTION ENGINE (SAME LOGIC YOU CHOSE)
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

        if (not self.raw_history) or (self.raw_history[0].get("issueNumber") != issue_data.get("issueNumber")):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:120]
            self.raw_history = self.raw_history[:120]

    def get_pattern_signal(self, current_streak_loss: int):
        if len(self.history) < 15:
            return random.choice(["BIG", "SMALL"])

        h = self.history
        votes = []

        last_12 = h[:12]
        votes.append("BIG" if last_12.count("BIG") > last_12.count("SMALL") else "SMALL")
        votes.append(h[0])  # dragon
        votes.append("SMALL" if h[0] == "BIG" else "BIG")  # reverse
        if h[0] == h[1] == h[2]:
            votes.append(h[0])
        if h[0] == h[1] and h[2] == h[3] and h[1] != h[2]:
            votes.append("SMALL" if h[0] == "BIG" else "BIG")

        try:
            r_num = int(self.raw_history[0].get("number", 0))
            p_digit = int(str(self.raw_history[0].get("issueNumber", 0))[-1])
            prev_num = int(self.raw_history[1].get("number", 0))

            votes.append("SMALL" if (p_digit + r_num) % 2 == 0 else "BIG")
            votes.append("SMALL" if (r_num + prev_num) % 2 == 0 else "BIG")
            votes.append("BIG" if r_num >= 5 else "SMALL")
            votes.append("SMALL" if ((r_num * 3) + p_digit) % 2 == 0 else "BIG")
        except Exception:
            pass

        current_pat = h[:3]
        match_big, match_small = 0, 0
        for i in range(1, len(h) - 3):
            if h[i:i+3] == current_pat:
                if h[i-1] == "BIG":
                    match_big += 1
                else:
                    match_small += 1
        if match_big > match_small:
            votes.append("BIG")
        elif match_small > match_big:
            votes.append("SMALL")

        votes.append(h[0])  # psych

        if current_streak_loss >= 2 and self.last_prediction:
            rec_vote = "SMALL" if self.last_prediction == "BIG" else "BIG"
            votes += [rec_vote, rec_vote, rec_vote]

        big_votes = votes.count("BIG")
        small_votes = votes.count("SMALL")
        if big_votes > small_votes:
            prediction = "BIG"
        elif small_votes > big_votes:
            prediction = "SMALL"
        else:
            prediction = h[0]

        if current_streak_loss >= 4:
            prediction = h[0]

        self.last_prediction = prediction
        return prediction

    def calc_confidence(self, streak_loss: int) -> int:
        base = random.randint(86, 93)
        if streak_loss >= 2:
            base = max(82, base - 2)
        if len(self.history) >= 3 and self.history[0] == self.history[1] == self.history[2]:
            base = min(96, base + 2)
        return base


# =========================
# BOT STATE
# =========================
def now_bd_str() -> str:
    return datetime.now(BD_TZ).strftime("%H:%M:%S")

def mode_label(mode: str) -> str:
    return "30 SEC" if mode == "30S" else "1 MIN"

@dataclass
class ActiveBet:
    predicted_issue: str
    pick: str
    checking_msg_ids: Dict[int, int] = field(default_factory=dict)
    loss_related_ids: Dict[int, List[int]] = field(default_factory=dict)

@dataclass
class BotState:
    running: bool = False
    mode: str = "30S"
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

    color_mode: bool = False
    graceful_stop_requested: bool = False

    stop_event: asyncio.Event = field(default_factory=asyncio.Event)

state = BotState()


# =========================
# NEW FETCH (CHANGED TO POST + typeId)
# =========================
API_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

def _fetch_latest_issue_sync(mode: str) -> Optional[dict]:
    """
    Returns dict with keys that engine expects:
    {
      "issueNumber": str,
      "number": int
    }
    """
    type_id = TYPEID_30S if mode == "30S" else TYPEID_1M

    payload = {
        "typeId": type_id,
        "pageSize": 1,
        "pageNo": 1,
    }

    try:
        r = requests.post(
            WIN_GO_API,
            data=payload,
            headers=API_HEADERS,
            timeout=FETCH_TIMEOUT
        )
        if r.status_code != 200:
            return None

        js = r.json()
        items = (js.get("data") or {}).get("list") or []
        if not items:
            return None

        row = items[0]
        issue = str(row.get("issueNumber"))
        num = int(row.get("number"))

        return {"issueNumber": issue, "number": num}
    except Exception:
        return None

async def fetch_latest_issue(mode: str) -> Optional[dict]:
    return await asyncio.to_thread(_fetch_latest_issue_sync, mode)


# =========================
# MESSAGE FORMAT
# =========================
def pretty_pick(pick: str) -> Tuple[str, str]:
    if pick == "BIG":
        return "🟢🟢 <b>BIG</b> 🟢🟢", "GREEN"
    return "🔴🔴 <b>SMALL</b> 🔴🔴", "RED"

def recovery_label(loss_streak: int) -> str:
    if loss_streak <= 0:
        return f"0 Step / {MAX_RECOVERY_STEPS}"
    return f"{loss_streak} Step Loss / {MAX_RECOVERY_STEPS}"

def format_signal(issue: str, pick: str, conf: int) -> str:
    pick_txt, _ = pretty_pick(pick)
    return (
        f"<b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>PREDICTION</b> ➜ {pick_txt}\n"
        f"📈 <b>Confidence</b> ➜ <b>{conf}%</b>\n"
        f"🧠 <b>Recovery</b> ➜ <b>{recovery_label(state.streak_loss)}</b>\n"
        f"⏱ <b>BD Time</b> ➜ <b>{now_bd_str()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>JOIN</b> ➜ <a href='{CHANNEL_LINK}'>{CHANNEL_LINK}</a>"
    )

def format_checking(wait_issue: str) -> str:
    return (
        f"🛰 <b>CHECKING RESULT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"🧾 <b>Waiting:</b> <code>{wait_issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ syncing..."
    )

def format_result(issue: str, res_num: str, res_type: str, pick: str, is_win: bool) -> str:
    pick_txt, _ = pretty_pick(pick)
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    color_result = "GREEN" if res_type == "BIG" else "RED"

    if is_win:
        header = "✅ <b>WIN CONFIRMED</b> ✅"
        extra = f"\n🎨 <b>Color Win:</b> <b>{color_result}</b>" if state.color_mode else ""
    else:
        header = "❌ <b>LOSS CONFIRMED</b> ❌"
        extra = ""

    return (
        f"{header}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{res_num} ({res_type})</b>\n"
        f"🎯 <b>Your Pick:</b> {pick_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 <b>Recovery:</b> <b>{recovery_label(state.streak_loss)}</b>\n"
        f"{extra}\n"
        f"📊 <b>W:</b> <b>{state.wins}</b> | <b>L:</b> <b>{state.losses}</b> | ⏱ <b>{now_bd_str()}</b>"
    ).strip()

def format_summary() -> str:
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"📦 <b>Total:</b> <b>{total}</b>\n"
        f"✅ <b>Win:</b> <b>{state.wins}</b>\n"
        f"❌ <b>Loss:</b> <b>{state.losses}</b>\n"
        f"🎯 <b>Win Rate:</b> <b>{wr:.1f}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>Max Win Streak:</b> <b>{state.max_win_streak}</b>\n"
        f"🧨 <b>Max Loss Streak:</b> <b>{state.max_loss_streak}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Closed:</b> <b>{now_bd_str()}</b>\n"
        f"🔗 <b>REJOIN</b> ➜ <a href='{CHANNEL_LINK}'>{CHANNEL_LINK}</a>"
    )


# =========================
# PANEL
# =========================
def panel_text() -> str:
    running = "🟢 RUNNING" if state.running else "🔴 STOPPED"
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
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
        "📊 <b>Live Stats</b>\n"
        f"✅ Win: <b>{state.wins}</b>\n"
        f"❌ Loss: <b>{state.losses}</b>\n"
        f"🎯 WinRate: <b>{wr:.1f}%</b>\n"
        f"🔥 WinStreak: <b>{state.streak_win}</b> | 🧊 LossStreak: <b>{state.streak_loss}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>Select then Start</i>"
    )

def panel_markup() -> InlineKeyboardMarkup:
    rows = [
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
# HELPERS
# =========================
async def safe_delete(bot, chat_id: int, msg_id: int):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
        pass

async def send_sticker(bot, sticker_id: str):
    try:
        await bot.send_sticker(state.selected_targets[0], sticker_id)
    except Exception:
        pass

async def send_message(bot, text: str) -> Optional[int]:
    try:
        m = await bot.send_message(
            state.selected_targets[0],
            text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return m.message_id
    except Exception:
        return None


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

    # delete checking + loss-related messages on stop
    if state.active:
        for mid in state.active.checking_msg_ids.values():
            await safe_delete(bot, state.selected_targets[0], mid)

        for mid in state.active.loss_related_ids.get(state.selected_targets[0], []):
            await safe_delete(bot, state.selected_targets[0], mid)

    # END sticker (required, not during loss)
    await send_sticker(bot, STICKERS["START_END_ALWAYS"])

    # summary
    await send_message(bot, format_summary())

    state.unlocked = False
    state.active = None
    state.graceful_stop_requested = False

async def start_session(bot, mode: str):
    state.mode = mode
    state.session_id += 1
    state.running = True
    state.stop_event.clear()
    state.graceful_stop_requested = False

    state.engine = PredictionEngine()
    state.active = None
    state.last_result_issue = None
    state.last_signal_issue = None
    reset_stats()

    # Start sticker per mode
    await send_sticker(bot, STICKERS["START_30S"] if mode == "30S" else STICKERS["START_1M"])
    # Always at start
    await send_sticker(bot, STICKERS["START_END_ALWAYS"])


# =========================
# ENGINE LOOP
# =========================
async def engine_loop(context: ContextTypes.DEFAULT_TYPE, my_session: int):
    bot = context.bot
    last_seen_issue = None

    while state.running and state.session_id == my_session:
        if state.stop_event.is_set() or (not state.running) or state.session_id != my_session:
            break

        latest = await fetch_latest_issue(state.mode)
        if not latest:
            await asyncio.sleep(FETCH_RETRY_SLEEP)
            continue

        issue = str(latest.get("issueNumber"))
        num_i = int(latest.get("number"))
        num = str(num_i)
        res_type = "BIG" if num_i >= 5 else "SMALL"
        next_issue = str(int(issue) + 1)

        state.engine.update_history(latest)

        if last_seen_issue == issue:
            await asyncio.sleep(0.12)
        last_seen_issue = issue

        # ---------- RESULT ----------
        if state.active and state.active.predicted_issue == issue:
            if state.last_result_issue == issue:
                await asyncio.sleep(0.05)
                continue

            pick = state.active.pick
            is_win = (pick == res_type)

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

            # STICKERS ORDER: WIN/LOSS + super win
            if is_win:
                await send_sticker(bot, STICKERS["WIN_ALWAYS"])
                if state.streak_win in STICKERS["SUPER_WIN"]:
                    await send_sticker(bot, STICKERS["SUPER_WIN"][state.streak_win])
                else:
                    await send_sticker(bot, random.choice(STICKERS["WIN_POOL"]))
                await send_sticker(bot, STICKERS["WIN_BIG"] if res_type == "BIG" else STICKERS["WIN_SMALL"])
                await send_sticker(bot, STICKERS["WIN_ANY"])
            else:
                await send_sticker(bot, STICKERS["LOSS"])

            await send_message(bot, format_result(issue, num, res_type, pick, is_win))

            # delete checking now
            for mid in state.active.checking_msg_ids.values():
                await safe_delete(bot, state.selected_targets[0], mid)

            state.last_result_issue = issue

            # graceful stop: stop only after a win
            if state.graceful_stop_requested and is_win:
                state.active = None
                await stop_session(bot, reason="graceful_done")
                break

            state.active = None

        # ---------- SIGNAL ----------
        if (not state.active) and (state.last_signal_issue != next_issue):
            if state.stop_event.is_set() or (not state.running) or state.session_id != my_session:
                break

            # Safety stop at 8 steps
            if state.streak_loss >= MAX_RECOVERY_STEPS:
                await send_message(
                    bot,
                    "🧊 <b>SAFETY STOP</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                    "Recovery 8 Step এ চলে গেছে। সেফটির জন্য সেশন বন্ধ করা হলো ✅",
                )
                await stop_session(bot, reason="max_steps")
                break

            pred = state.engine.get_pattern_signal(state.streak_loss)
            conf = state.engine.calc_confidence(state.streak_loss)

            # Sticker first
            if state.mode == "30S":
                s_stk = STICKERS["PRED_30S_BIG"] if pred == "BIG" else STICKERS["PRED_30S_SMALL"]
            else:
                s_stk = STICKERS["PRED_1M_BIG"] if pred == "BIG" else STICKERS["PRED_1M_SMALL"]

            await send_sticker(bot, s_stk)

            if state.color_mode:
                await send_sticker(bot, STICKERS["COLOR_GREEN"] if pred == "BIG" else STICKERS["COLOR_RED"])

            # Prediction msg then checking msg
            await send_message(bot, format_signal(next_issue, pred, conf))

            checking_id = await send_message(bot, format_checking(next_issue))
            bet = ActiveBet(predicted_issue=next_issue, pick=pred)

            if checking_id:
                bet.checking_msg_ids[state.selected_targets[0]] = checking_id
                bet.loss_related_ids.setdefault(state.selected_targets[0], []).append(checking_id)

            state.active = bet
            state.last_signal_issue = next_issue

        await asyncio.sleep(FAST_LOOP_30S if state.mode == "30S" else FAST_LOOP_1M)


# =========================
# COMMANDS & CALLBACKS
# =========================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.expected_password = await get_live_password()
    state.unlocked = False

    await update.message.reply_text(
        "🔒 <b>SYSTEM LOCKED</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Password দিন:",
        parse_mode=ParseMode.HTML
    )

async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state.unlocked:
        state.expected_password = await get_live_password()
        await update.message.reply_text("🔒 <b>LOCKED</b>\nPassword দিন:", parse_mode=ParseMode.HTML)
        return

    await update.message.reply_text(
        panel_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=panel_markup(),
        disable_web_page_preview=True
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()

    if not state.unlocked:
        state.expected_password = await get_live_password()
        if txt == state.expected_password:
            state.unlocked = True
            await update.message.reply_text("✅ <b>UNLOCKED</b>", parse_mode=ParseMode.HTML)
            await update.message.reply_text(
                panel_text(),
                parse_mode=ParseMode.HTML,
                reply_markup=panel_markup(),
                disable_web_page_preview=True
            )
        else:
            await update.message.reply_text("❌ <b>WRONG PASSWORD</b>", parse_mode=ParseMode.HTML)
        return

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""

    if not state.unlocked:
        await q.edit_message_text("🔒 <b>LOCKED</b>\n/start দিন।", parse_mode=ParseMode.HTML)
        return

    if data == "REFRESH_PANEL":
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=panel_markup())
        return

    if data == "TOGGLE_COLOR":
        state.color_mode = not state.color_mode
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=panel_markup())
        return

    if data.startswith("START:"):
        mode = data.split(":", 1)[1]
        if state.running:
            await stop_session(context.bot, reason="restart")

        await start_session(context.bot, mode)
        my_session = state.session_id
        context.application.create_task(engine_loop(context, my_session))

        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=panel_markup())
        return

    if data == "STOP:FORCE":
        if state.running:
            await stop_session(context.bot, reason="force")
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=panel_markup())
        return

    if data == "STOP:GRACEFUL":
        if state.running:
            state.graceful_stop_requested = True
            if state.streak_loss == 0 and state.active is None:
                await stop_session(context.bot, reason="graceful_now")
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=panel_markup())
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
