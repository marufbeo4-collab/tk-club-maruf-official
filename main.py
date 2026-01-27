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
BOT_TOKEN = "8456002611:AAFtqxTZ54FTUJNquuG85JDhMsZPYq3MM-U"  # ✅ নতুন টোকেন দিন (Revoke old token)

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

# API CONFIG (1M)
API_URL = "https://api880.inpay88.net/api/webapi/GetNoaverageEmerdList"

# BD Time
BD_TZ = timezone(timedelta(hours=6))

# Password source A1
PASSWORD_SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
PASSWORD_SHEET_GID = "0"
PASSWORD_FALLBACK = "2222"

# Settings
MAX_RECOVERY_STEPS = 8
FETCH_TIMEOUT = 6.0

# =========================
# STICKERS (OLD + NEW)
# =========================
STICKERS = {
    # -------------------------
    # OLD Prediction (1M)
    # -------------------------
    "PRED_1M_BIG_OLD": "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    "PRED_1M_SMALL_OLD": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",

    # OLD Color stickers (kept)
    "COLOR_RED_OLD": "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    "COLOR_GREEN_OLD": "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",

    # -------------------------
    # NEW Session start (MUST SEND)
    # -------------------------
    "SESSION_PRESTART": "CAACAgUAAxkBAAEQWbVpeJdAC4ezowY1slx0adINWawqRQAClRYAAvpg4FTYgDvCMotu1DgE",
    "SESSION_START_SEQ": [
        "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA",
        "CAACAgUAAxkBAAEQTkJpcmYz7CETjTbVuTaTloOWj0w1NgACrxkAAg8OoVfAIXjvhcHVhDgE",
        "CAACAgUAAxkBAAEQWbhpeJdF_GDrVMFmoDDmnqS74GMb5wACQBsAAqP3IFfZd1e-pXZaHDgE",
        "CAACAgUAAxkBAAEQWcdpeJdPqChaww0JErr0kn2VXkAvdAACmRUAAi_LIVccdiGIYpPZdDgE",
        "CAACAgUAAxkBAAEQWc9peJg6qnOLGfsK-_GLG-qGb-z4FAACuBYAAsnBmFSnBxgoKMV0zTgE",
    ],

    # -------------------------
    # NEW Prediction set (alternate)
    # -------------------------
    "PRED_BIG_NEW": "CAACAgUAAxkBAAEQWb1peJdIq-Oq2r5tadtbwIn8hJbtVgAC5hcAAkBuIVf-60HIJ4L9tzgE",
    "PRED_SMALL_NEW": "CAACAgUAAxkBAAEQWb5peJdIXa96Z29KBL7Irg-7YEG67wACZRoAAsDBIVc_bllpQcf52jgE",
    "COLOR_RED_NEW": "CAACAgUAAxkBAAEQWcJpeJdKIJP8aovK9UrPBLXvWlvFLQACQxsAAiyRIFdg8_K_Uoi6qDgE",
    "COLOR_GREEN_NEW": "CAACAgUAAxkBAAEQWcFpeJdKf82jvSdW8pnpqOVBrBNvfwAC8hUAAojDIFc9fDJEqFMfRzgE",

    # -------------------------
    # OLD Start stickers (kept)
    # -------------------------
    "START_1M_OLD": "CAACAgUAAxkBAAEQUrRpdYvESSIrn4-Lm936I6F8_BaN-wACChYAAuBHOVc6YQfcV-EKqjgE",
    "START_END_ALWAYS_OLD": "CAACAgUAAxkBAAEQTjRpcmWdzXBzA7e9KNz8QgTI6NXlxgACuRcAAh2x-FaJNjq4QG_DujgE",

    # -------------------------
    # WIN stickers (old kept + new win extra)
    # -------------------------
    "WIN_BIG": "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    "WIN_SMALL": "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    "WIN_ALWAYS": "CAACAgUAAxkBAAEQUTZpdFC4094KaOEdiE3njwhAGVCuBAAC4hoAAt0EqVQXmdKVLGbGmzgE",
    "WIN_ANY": "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA",

    "WIN_EXTRA_NEW": "CAACAgUAAxkBAAEQWctpeJdTTmIB7FFU1RgNNxaBs5FtggACDxgAAgTqOVf77zJ4WoeanjgE",

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
        5: "CAACAgUAAxkBAAEQTiNpcmUgu_dP3wKT2k94EJCiw3u52QACihoAArkfqFSlrldtXbLGGDgE",
        6: "CAACAgUAAxkBAAEQTiRpcmUhQJUjd2ukdtfEtBjwtMH4MAACWRgAAsTFqVTato0SmSN-6jgE",
        7: "CAACAgUAAxkBAAEQTiVpcmUhha9HAAF19fboYayfUrm3tdYAAioXAAIHgKhUD0QmGyF5Aug4BA",
        8: "CAACAgUAAxkBAAEQTixpcmUmevnNEqUbr0qbbVgW4psMNQACMxUAAow-qFSnSz4Ik1ddNzgE",
        9: "CAACAgUAAxkBAAEQTi1pcmUmpSxAHo2pvR-GjCPTmkLr0AACLh0AAhCRqFRH5-2YyZKq1jgE",
        10: "CAACAgUAAxkBAAEQTi5pcmUmjmjp7oXg4InxI1dGYruxDwACqBgAAh19qVT6X_-oEywCkzgE",
    },

    # -------------------------
    # NEW Session end (MUST AFTER SUMMARY)
    # -------------------------
    "SESSION_END_AFTER_SUMMARY": "CAACAgUAAxkBAAEQWdBpeJg6sivWL9tmO0J1ylmxlZCt4QAC8RIAAsRkoFQZsT3pks7C0jgE",
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
# PREDICTION ENGINE (DYNAMIC MIRROR LOGIC) ✅ YOUR LOGIC
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

    def calc_confidence(self, streak_loss):
        base = random.randint(93, 98)
        return max(50, base - (streak_loss * 5))

    def get_pattern_signal(self, current_streak_loss):
        if not self.history:
            return random.choice(["BIG", "SMALL"])

        h = self.history
        last_result = h[0]

        # STEP 3: EMERGENCY SAFETY (LOSS 5+)
        if current_streak_loss >= 5:
            return last_result

        # STEP 1: PATTERN DETECTION
        if len(h) >= 2 and h[0] != h[1]:
            prediction = "SMALL" if last_result == "BIG" else "BIG"
        else:
            prediction = last_result

        # STEP 2: MIRROR TRAP FIX (LOSS 2-4)
        if current_streak_loss >= 2:
            prediction = "SMALL" if prediction == "BIG" else "BIG"

        return prediction


# =========================
# BOT STATE
# =========================
def now_bd_str() -> str:
    return datetime.now(BD_TZ).strftime("%I:%M:%S %p")

def calc_current_1m_period(now: datetime) -> str:
    date_str = now.strftime("%Y%m%d")
    total_slots = (now.hour * 60) + now.minute + 1
    return f"{date_str}01{total_slots:04d}"

@dataclass
class ActiveBet:
    predicted_issue: str
    pick: str
    checking_msg_ids: Dict[int, int] = field(default_factory=dict)

@dataclass
class BotState:
    running: bool = False
    session_id: int = 0
    engine: PredictionEngine = field(default_factory=PredictionEngine)
    active: Optional[ActiveBet] = None
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
    color_mode: bool = True  # ✅ আপনি চাইলে panel থেকে toggle করে OFF করতে পারবেন
    graceful_stop_requested: bool = False
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)

state = BotState()


# =========================
# FETCH (1M typeId=1)
# =========================
def _fetch_latest_issue_sync() -> Optional[dict]:
    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": 1,  # ✅ ONLY 1 MIN
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
# STICKER SELECTOR (NO DOUBLE FOR PRED)
# =========================
def choose_pred_stickers(pick: str) -> Tuple[str, Optional[str]]:
    """
    ✅ Prediction sticker = either OLD set OR NEW set (not both)
    ✅ Color sticker (if enabled) = same set only (not both)
    """
    use_new = (random.random() < 0.35)  # 35% নতুন সেট, বাকিটা পুরানো (আপনি চাইলে বাড়াবেন)
    if use_new:
        pred = STICKERS["PRED_BIG_NEW"] if pick == "BIG" else STICKERS["PRED_SMALL_NEW"]
        color = STICKERS["COLOR_GREEN_NEW"] if pick == "BIG" else STICKERS["COLOR_RED_NEW"]
        return pred, color
    else:
        pred = STICKERS["PRED_1M_BIG_OLD"] if pick == "BIG" else STICKERS["PRED_1M_SMALL_OLD"]
        color = STICKERS["COLOR_GREEN_OLD"] if pick == "BIG" else STICKERS["COLOR_RED_OLD"]
        return pred, color


# =========================
# MESSAGES (SHORT + STYLISH + BANGLA MARKETING)
# =========================
def pick_line(pick: str) -> str:
    return "🟢 <b>BIG</b>" if pick == "BIG" else "🔴 <b>SMALL</b>"

def market_line() -> str:
    return (
        f"📌 <b>মার্কেটিং:</b> এই লিংকে একাউন্ট খুলে <b>ডিপোজিট</b> করুন এবং "
        f"<b>VIP</b> তে এর চেয়েও ভালো <b>হ্যাক</b> নিন 👉 <a href='{REG_LINK}'>OPEN ACCOUNT</a>"
    )

def format_signal(issue: str, pick: str, conf: int) -> str:
    return (
        f"{BRAND_NAME}\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"🎯 <b>Entry:</b> {pick_line(pick)}  |  🔥 <b>{conf}%</b>\n"
        f"🧠 <b>Recovery:</b> <b>{state.streak_loss}/{MAX_RECOVERY_STEPS}</b>  |  🕒 <b>{now_bd_str()}</b>\n"
        f"{market_line()}\n"
        f"👤 <b>Owner:</b> {OWNER_USERNAME}"
    )

def format_checking(wait_issue: str) -> str:
    return (
        f"⏳ <b>Result Checking...</b>  |  <code>{wait_issue}</code>\n"
        f"🕒 <b>{now_bd_str()}</b>"
    )

def format_result(issue: str, res_num: str, res_type: str, pick: str, is_win: bool) -> str:
    head = "✅ <b>WIN</b>" if is_win else "❌ <b>LOSS</b>"
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    return (
        f"{head}  |  🧾 <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{res_num} ({res_type})</b>\n"
        f"🎯 <b>Your Pick:</b> {pick_line(pick)}\n"
        f"📊 <b>W:</b> {state.wins}  |  <b>L:</b> {state.losses}  |  🕒 <b>{now_bd_str()}</b>\n"
        f"{market_line()}"
    )

def format_summary() -> str:
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    return (
        "🛑 <b>SESSION CLOSED</b>\n"
        f"📦 <b>Total:</b> {total}  |  ✅ <b>Win:</b> {state.wins}  |  ❌ <b>Loss:</b> {state.losses}\n"
        f"🎯 <b>WinRate:</b> {wr:.1f}%  |  🔥 <b>MaxWin:</b> {state.max_win_streak}  |  🧨 <b>MaxLoss:</b> {state.max_loss_streak}\n"
        f"🕒 <b>Closed:</b> {now_bd_str()}\n"
        f"📣 <b>VIP:</b> <a href='{CHANNEL_LINK}'>JOIN</a>  |  👤 <b>Owner:</b> {OWNER_USERNAME}"
    )


# =========================
# PANEL
# =========================
def _chat_name(chat_id: int) -> str:
    if chat_id == TARGETS["MAIN_GROUP"]:
        return "MAIN GROUP"
    if chat_id == TARGETS["VIP"]:
        return "VIP"
    if chat_id == TARGETS["PUBLIC"]:
        return "PUBLIC"
    return str(chat_id)

def panel_text() -> str:
    running = "🟢 RUNNING" if state.running else "🔴 STOPPED"
    sel = state.selected_targets[:] if state.selected_targets else [TARGETS["MAIN_GROUP"]]
    sel_lines = "\n".join([f"✅ <b>{_chat_name(cid)}</b> <code>{cid}</code>" for cid in sel])
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    color = "🎨 <b>Color:</b> ON" if state.color_mode else "🎨 <b>Color:</b> OFF"
    grace = "🧠 <b>Stop After Win:</b> ✅" if state.graceful_stop_requested else "🧠 <b>Stop After Win:</b> ❌"
    return (
        "🔐 <b>CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Status:</b> {running}\n"
        f"{color}\n"
        f"{grace}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>Send Signals To</b>\n"
        f"{sel_lines}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Stats:</b> ✅ {state.wins} | ❌ {state.losses} | 🎯 {wr:.1f}%\n"
        f"🔥 <b>Streak:</b> W {state.streak_win} | L {state.streak_loss}\n"
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
        [InlineKeyboardButton("🎨 Color: ON" if state.color_mode else "🎨 Color: OFF", callback_data="TOGGLE_COLOR")],
        [InlineKeyboardButton("⚡ Start 1 MIN VIP", callback_data="START:1M")],
        [InlineKeyboardButton("🧠 Stop After Win", callback_data="STOP:GRACEFUL"),
         InlineKeyboardButton("🛑 Stop Now", callback_data="STOP:FORCE")],
        [InlineKeyboardButton("🔄 Refresh Panel", callback_data="REFRESH_PANEL")],
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

    # delete "checking"
    if state.active:
        for cid, mid in (state.active.checking_msg_ids or {}).items():
            await safe_delete(bot, cid, mid)

    # Summary first
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

    # Then END sticker MUST
    await broadcast_sticker(bot, STICKERS["SESSION_END_AFTER_SUMMARY"])

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
    state.last_signal_issue = None
    reset_stats()

    # ✅ MUST: Pre-start sticker before prediction starts
    await broadcast_sticker(bot, STICKERS["SESSION_PRESTART"])

    # ✅ MUST: Start sticker sequence
    for s in STICKERS["SESSION_START_SEQ"]:
        await broadcast_sticker(bot, s)

    # Kept old start signals too (optional but kept)
    await broadcast_sticker(bot, STICKERS["START_1M_OLD"])
    await broadcast_sticker(bot, STICKERS["START_END_ALWAYS_OLD"])


# =========================
# ENGINE LOOP (1 MIN ONLY)
# =========================
async def engine_loop(context: ContextTypes.DEFAULT_TYPE, my_session: int):
    bot = context.bot

    while state.running and state.session_id == my_session:
        if state.stop_event.is_set():
            break

        now = datetime.now(BD_TZ)
        sec = now.second

        current_running_period = calc_current_1m_period(now)

        # ✅ safe window: 05-40 sec (late কম হবে)
        is_safe_time = (5 <= sec <= 40)

        # 1) fetch latest closed result
        latest_data = await fetch_latest_issue()
        if latest_data:
            state.engine.update_history(latest_data)

            latest_issue = str(latest_data.get("issueNumber"))
            latest_num = str(latest_data.get("number"))
            latest_type = "BIG" if int(latest_data.get("number")) >= 5 else "SMALL"

            if state.active and state.active.predicted_issue == latest_issue:
                pick = state.active.pick
                is_win = (pick == latest_type)

                # delete checking msgs
                for cid, mid in (state.active.checking_msg_ids or {}).items():
                    await safe_delete(bot, cid, mid)

                if is_win:
                    state.wins += 1
                    state.streak_win += 1
                    state.streak_loss = 0
                    state.max_win_streak = max(state.max_win_streak, state.streak_win)

                    await broadcast_sticker(bot, STICKERS["WIN_ALWAYS"])

                    if state.streak_win in STICKERS["SUPER_WIN"]:
                        await broadcast_sticker(bot, STICKERS["SUPER_WIN"][state.streak_win])
                    else:
                        await broadcast_sticker(bot, random.choice(STICKERS["WIN_POOL"]))

                    await broadcast_sticker(bot, STICKERS["WIN_BIG"] if latest_type == "BIG" else STICKERS["WIN_SMALL"])
                    await broadcast_sticker(bot, STICKERS["WIN_ANY"])

                    # ✅ MUST: new win sticker also
                    await broadcast_sticker(bot, STICKERS["WIN_EXTRA_NEW"])
                else:
                    state.losses += 1
                    state.streak_loss += 1
                    state.streak_win = 0
                    state.max_loss_streak = max(state.max_loss_streak, state.streak_loss)
                    await broadcast_sticker(bot, STICKERS["LOSS"])

                await broadcast_message(
                    bot,
                    format_result(latest_issue, latest_num, latest_type, pick, is_win)
                )

                state.active = None

                if state.graceful_stop_requested and is_win:
                    await stop_session(bot, reason="graceful_done")
                    break

        # 2) signal generation
        if (not state.active) and is_safe_time:
            if state.last_signal_issue != current_running_period:

                if state.streak_loss >= MAX_RECOVERY_STEPS:
                    await broadcast_message(bot, "🧊 <b>SAFETY STOP</b>\n<i>Recovery limit reached.</i>")
                    await stop_session(bot, reason="max_steps")
                    break

                pred = state.engine.get_pattern_signal(state.streak_loss)
                conf = state.engine.calc_confidence(state.streak_loss)

                pred_stk, color_stk = choose_pred_stickers(pred)

                # ✅ prediction stickers: only ONE set (old or new)
                await broadcast_sticker(bot, pred_stk)

                # ✅ color: only ONE sticker (same set) and only if enabled
                if state.color_mode and color_stk:
                    await broadcast_sticker(bot, color_stk)

                # send signal msg
                await broadcast_message(bot, format_signal(current_running_period, pred, conf))

                # checking message
                checking_ids = {}
                for cid in state.selected_targets:
                    try:
                        m = await bot.send_message(cid, format_checking(current_running_period), parse_mode=ParseMode.HTML)
                        checking_ids[cid] = m.message_id
                    except Exception:
                        pass

                state.active = ActiveBet(predicted_issue=current_running_period, pick=pred, checking_msg_ids=checking_ids)
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

    if data == "TOGGLE_COLOR":
        state.color_mode = not state.color_mode
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
            # stop only after next WIN (or immediate if idle + no loss)
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
