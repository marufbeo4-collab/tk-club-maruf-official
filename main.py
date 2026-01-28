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
# CONFIG
# =========================
BOT_TOKEN = "8456002611:AAFtqxTZ54FTUJNquuG85JDhMsZPYq3MM-U"

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
FETCH_TIMEOUT = 6.0

# =========================
# AUTO SCHEDULE (BD TIME)
# =========================
AUTO_WINDOWS = [
    ("21:00", "21:30"),
    ("23:00", "23:30"),
    ("10:00", "10:30"),
    ("12:00", "12:30"),
    ("15:00", "15:30"),
    ("19:00", "19:30"),
]


def _hhmm_to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


AUTO_WINDOWS_MIN = [(_hhmm_to_minutes(a), _hhmm_to_minutes(b)) for a, b in AUTO_WINDOWS]


def is_now_in_any_window(now: datetime) -> bool:
    mins = now.hour * 60 + now.minute
    for a, b in AUTO_WINDOWS_MIN:
        if a <= mins < b:
            return True
    return False


# =========================
# STICKERS (OLD + NEW)
# =========================
STICKERS = {
    # OLD PRED (1M)
    "PRED_1M_BIG_OLD": "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    "PRED_1M_SMALL_OLD": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",
    "COLOR_RED_OLD": "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    "COLOR_GREEN_OLD": "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",

    # NEW Session start (MUST)
    "SESSION_PRESTART": "CAACAgUAAxkBAAEQWbVpeJdAC4ezowY1slx0adINWawqRQAClRYAAvpg4FTYgDvCMotu1DgE",
    "SESSION_START_SEQ": [
        "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA",
        "CAACAgUAAxkBAAEQTkJpcmYz7CETjTbVuTaTloOWj0w1NgACrxkAAg8OoVfAIXjvhcHVhDgE",
        "CAACAgUAAxkBAAEQWbhpeJdF_GDrVMFmoDDmnqS74GMb5wACQBsAAqP3IFfZd1e-pXZaHDgE",
        "CAACAgUAAxkBAAEQWcdpeJdPqChaww0JErr0kn2VXkAvdAACmRUAAi_LIVccdiGIYpPZdDgE",
        "CAACAgUAAxkBAAEQWc9peJg6qnOLGfsK-_GLG-qGb-z4FAACuBYAAsnBmFSnBxgoKMV0zTgE",
    ],

    # NEW Prediction set (alternate)
    "PRED_BIG_NEW": "CAACAgUAAxkBAAEQWb1peJdIq-Oq2r5tadtbwIn8hJbtVgAC5hcAAkBuIVf-60HIJ4L9tzgE",
    "PRED_SMALL_NEW": "CAACAgUAAxkBAAEQWb5peJdIXa96Z29KBL7Irg-7YEG67wACZRoAAsDBIVc_bllpQcf52jgE",
    "COLOR_RED_NEW": "CAACAgUAAxkBAAEQWcJpeJdKIJP8aovK9UrPBLXvWlvFLQACQxsAAiyRIFdg8_K_Uoi6qDgE",
    "COLOR_GREEN_NEW": "CAACAgUAAxkBAAEQWcFpeJdKf82jvSdW8pnpqOVBrBNvfwAC8hUAAojDIFc9fDJEqFMfRzgE",

    # WIN/Loss (Old kept)
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

    # End sticker after summary (MUST)
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
# PREDICTION ENGINE (UPDATED: HYBRID REVERSE LOGIC)
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
        # লস হলে কনফিডেন্স একটু কমিয়ে দেখাবে
        return max(45, base - (streak_loss * 8))

    def get_pattern_signal(self, current_streak_loss):
        # ইতিহাস খুব ছোট হলে র‍্যান্ডম
        if len(self.history) < 6:
            return random.choice(["BIG", "SMALL"])

        last_result = self.history[0]
        recent = self.history[:5]
        
        # ডিফল্ট প্রেডিকশন (Logic Base)
        prediction = None

        # ১. প্যাটার্ন চেক (Pattern Analysis)
        # Dragon (Last 3 same)
        if recent[0] == recent[1] == recent[2]:
            prediction = recent[0]
        # ZigZag (ABAB)
        elif recent[0] != recent[1] and recent[1] != recent[2]:
            prediction = "SMALL" if recent[0] == "BIG" else "BIG"
        # 2-2 Pattern (AABB)
        elif recent[0] == recent[1] and recent[2] == recent[3] and recent[1] != recent[2]:
            prediction = "SMALL" if recent[0] == "BIG" else "BIG"
        else:
            # ডিফল্ট ট্রেন্ড (Last Result)
            prediction = last_result

        # =========================================================
        # ⚠️ THE FIX: INVERSE LOGIC ADAPTER
        # =========================================================
        
        # ধাপ ১: যদি টানা ২ বা তার বেশি লস হয়, তার মানে মার্কেট উল্টো চলছে।
        # তখন আমরা সাধারণ লজিকের "বিপরীত" (Reverse) ধরব।
        if current_streak_loss >= 2:
            prediction = "SMALL" if prediction == "BIG" else "BIG"

        # ধাপ ২: যদি আল্লাহ না করুক ৫ বার লস হয়, তার মানে মার্কেট খুব বাজে (Dragon Trap)।
        # তখন আমরা আর প্যাটার্ন দেখব না, সোজা লাস্ট রেজাল্ট কপি করব (Trend Follow)।
        if current_streak_loss >= 5:
            prediction = last_result

        self.last_prediction = prediction
        return prediction

# =========================
# STATE
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

    # ✅ Default: Color OFF always
    color_mode: bool = False

    # ✅ Auto schedule default ON
    auto_schedule_enabled: bool = True

    # Track schedule-started sessions
    started_by_schedule: bool = False

    graceful_stop_requested: bool = False
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)

state = BotState()

# =========================
# FETCH (1 MIN ONLY, typeId=1)
# =========================
def _fetch_latest_issue_sync() -> Optional[dict]:
    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": 1,
        "language": 0,
        "random": "4ec1d2c67364426aa056214302636756",
        "signature": "D39F9069695C55720235791E0D10D695",
        "timestamp": int(time.time()),
    }
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Origin": "https://dkwin9.com",
        "Referer": "https://dkwin9.com/",
    }
    try:
        r = requests.post(API_URL, json=payload, headers=headers, timeout=FETCH_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if data and "data" in data and "list" in data["data"] and data["data"]["list"]:
                return data["data"]["list"][0]
    except Exception as e:
        print("API Error:", e)
    return None

async def fetch_latest_issue() -> Optional[dict]:
    return await asyncio.to_thread(_fetch_latest_issue_sync)

# =========================
# STICKER PICKER (one set only)
# =========================
def choose_pred_stickers(pick: str) -> Tuple[str, Optional[str]]:
    use_new = (random.random() < 0.35)  # sometimes new
    if use_new:
        pred = STICKERS["PRED_BIG_NEW"] if pick == "BIG" else STICKERS["PRED_SMALL_NEW"]
        color = STICKERS["COLOR_GREEN_NEW"] if pick == "BIG" else STICKERS["COLOR_RED_NEW"]
        return pred, color
    pred = STICKERS["PRED_1M_BIG_OLD"] if pick == "BIG" else STICKERS["PRED_1M_SMALL_OLD"]
    color = STICKERS["COLOR_GREEN_OLD"] if pick == "BIG" else STICKERS["COLOR_RED_OLD"]
    return pred, color

# =========================
# PREMIUM MESSAGES (your style)
# =========================
def pick_badge(pick: str) -> str:
    return "🟢 <b>BIG</b>" if pick == "BIG" else "🔴 <b>SMALL</b>"

def color_badge_from_pick(pick: str) -> str:
    return "🟩 <b>GREEN</b>" if pick == "BIG" else "🟥 <b>RED</b>"

def marketing_block() -> str:
    return (
        "📌 <b>বিঃদ্রঃ:</b> এই লিংকে একাউন্ট খুলে <b>ডিপোজিট</b> করুন, "
        "আর <b>VIP</b> তে এর চেয়েও ভালো <b>হ্যাক</b> নিন 👇\n"
        f"🔗 <b><a href='{REG_LINK}'>REGISTRATION LINK</a></b>"
    )

def format_signal(issue: str, pick: str, conf: int) -> str:
    entry_line = f"🎯 <b>Entry:</b> {pick_badge(pick)}"
    if state.color_mode:
        entry_line += f"  |  {color_badge_from_pick(pick)}"

    return (
        f"{BRAND_NAME}\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"{entry_line}\n"
        f"✨ <b>Confidence:</b> 🔥 <b>{conf}%</b>\n"
        f"🧠 <b>Recovery:</b> <b>{state.streak_loss}/{MAX_RECOVERY_STEPS}</b>\n"
        f"🕒 <b>{now_bd_str()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{marketing_block()}\n"
        f"👤 <b>Owner:</b> {OWNER_USERNAME}"
    )

def format_checking(wait_issue: str) -> str:
    return (
        f"⏳ <b>Result Checking...</b>\n"
        f"🧾 <b>Period:</b> <code>{wait_issue}</code>\n"
        f"🕒 <b>{now_bd_str()}</b>"
    )

def format_result(issue: str, res_num: str, res_type: str, pick: str, is_win: bool) -> str:
    head = "✅ <b>WIN CONFIRMED</b>" if is_win else "❌ <b>LOSS CONFIRMED</b>"
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    return (
        f"{head}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{res_num} ({res_type})</b>\n"
        f"🎯 <b>Your Pick:</b> {pick_badge(pick)}\n"
        f"📊 <b>W:</b> <b>{state.wins}</b>  |  <b>L:</b> <b>{state.losses}</b>\n"
        f"🕒 <b>{now_bd_str()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{marketing_block()}"
    )

def format_summary() -> str:
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    return (
        "🛑 <b>SESSION SUMMARY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Total:</b> <b>{total}</b>\n"
        f"✅ <b>Win:</b> <b>{state.wins}</b>\n"
        f"❌ <b>Loss:</b> <b>{state.losses}</b>\n"
        f"🎯 <b>Win Rate:</b> <b>{wr:.1f}%</b>\n"
        f"🔥 <b>Max Win Streak:</b> <b>{state.max_win_streak}</b>\n"
        f"🧨 <b>Max Loss Streak:</b> <b>{state.max_loss_streak}</b>\n"
        f"🕒 <b>Closed:</b> <b>{now_bd_str()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📣 <b>VIP:</b> <b><a href='{CHANNEL_LINK}'>JOIN NOW</a></b>\n"
        f"👤 <b>Owner:</b> {OWNER_USERNAME}"
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
    auto = "⏰ <b>Auto Schedule:</b> ON" if state.auto_schedule_enabled else "⏰ <b>Auto Schedule:</b> OFF"
    origin = "🧩 <b>Session:</b> AUTO" if (state.running and state.started_by_schedule) else "🧩 <b>Session:</b> MANUAL"

    windows = " | ".join([f"{a}-{b}" for a, b in AUTO_WINDOWS])

    return (
        "🔐 <b>CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Status:</b> {running}\n"
        f"{origin}\n"
        f"{color}\n"
        f"{auto}\n"
        f"🗓 <b>Schedule:</b> <i>{windows}</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>Send Signals To</b>\n"
        f"{sel_lines}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Stats:</b> ✅ <b>{state.wins}</b> | ❌ <b>{state.losses}</b> | 🎯 <b>{wr:.1f}%</b>\n"
        f"🔥 <b>Streak:</b> W <b>{state.streak_win}</b> | L <b>{state.streak_loss}</b>\n"
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
        [InlineKeyboardButton("⏰ Auto: ON" if state.auto_schedule_enabled else "⏰ Auto: OFF", callback_data="TOGGLE_AUTO")],
        [InlineKeyboardButton("⚡ Start 1 MIN", callback_data="START:1M")],
        [
            InlineKeyboardButton("🧠 Stop After Win", callback_data="STOP:GRACEFUL"),
            InlineKeyboardButton("🛑 Stop Now", callback_data="STOP:FORCE"),
        ],
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

    if state.active:
        for cid, mid in (state.active.checking_msg_ids or {}).items():
            await safe_delete(bot, cid, mid)

    # Summary first
    for cid in state.selected_targets:
        try:
            await bot.send_message(cid, format_summary(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except Exception:
            pass

    # End sticker MUST after summary
    await broadcast_sticker(bot, STICKERS["SESSION_END_AFTER_SUMMARY"])

    state.active = None
    state.graceful_stop_requested = False
    state.started_by_schedule = False

async def start_session(bot, started_by_schedule: bool):
    state.session_id += 1
    state.running = True
    state.stop_event.clear()
    state.graceful_stop_requested = False
    state.engine = PredictionEngine()
    state.active = None
    state.last_signal_issue = None
    state.started_by_schedule = started_by_schedule

    # ✅ always default color OFF when session starts
    state.color_mode = False

    reset_stats()

    # MUST: prestart + start seq
    await broadcast_sticker(bot, STICKERS["SESSION_PRESTART"])
    for s in STICKERS["SESSION_START_SEQ"]:
        await broadcast_sticker(bot, s)

# =========================
# ENGINE LOOP (FIXED: no "prediction then instant win" mix)
# =========================
async def engine_loop(app: Application, my_session: int):
    bot = app.bot

    while state.running and state.session_id == my_session:
        if state.stop_event.is_set():
            break

        now = datetime.now(BD_TZ)
        sec = now.second
        current_period = calc_current_1m_period(now)

        # safe window for signal send
        is_safe_time = (5 <= sec <= 40)

        resolved_this_tick = False

        # 1) RESULT PROCESS FIRST
        latest_data = await fetch_latest_issue()
        if latest_data:
            state.engine.update_history(latest_data)
            latest_issue = str(latest_data.get("issueNumber"))
            latest_num = str(latest_data.get("number"))
            latest_type = "BIG" if int(latest_data.get("number")) >= 5 else "SMALL"

            if state.active and state.active.predicted_issue == latest_issue:
                pick = state.active.pick
                is_win = (pick == latest_type)

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
                    await broadcast_sticker(bot, STICKERS["WIN_EXTRA_NEW"])
                else:
                    state.losses += 1
                    state.streak_loss += 1
                    state.streak_win = 0
                    state.max_loss_streak = max(state.max_loss_streak, state.streak_loss)
                    await broadcast_sticker(bot, STICKERS["LOSS"])

                await broadcast_message(bot, format_result(latest_issue, latest_num, latest_type, pick, is_win))

                state.active = None
                resolved_this_tick = True

                if state.graceful_stop_requested and is_win:
                    await stop_session(bot, reason="graceful_done")
                    break

        # 2) SIGNAL GENERATION
        if (not state.active) and is_safe_time and (not resolved_this_tick):
            if state.last_signal_issue != current_period:
                if state.streak_loss >= MAX_RECOVERY_STEPS:
                    await broadcast_message(bot, "🧊 <b>SAFETY STOP</b>\n<i>Recovery limit reached.</i>")
                    await stop_session(bot, reason="max_steps")
                    break

                pred = state.engine.get_pattern_signal(state.streak_loss)
                conf = state.engine.calc_confidence(state.streak_loss)

                pred_stk, color_stk = choose_pred_stickers(pred)
                await broadcast_sticker(bot, pred_stk)

                if state.color_mode and color_stk:
                    await broadcast_sticker(bot, color_stk)

                await broadcast_message(bot, format_signal(current_period, pred, conf))

                checking_ids = {}
                for cid in state.selected_targets:
                    try:
                        m = await bot.send_message(cid, format_checking(current_period), parse_mode=ParseMode.HTML)
                        checking_ids[cid] = m.message_id
                    except Exception:
                        pass

                state.active = ActiveBet(predicted_issue=current_period, pick=pred, checking_msg_ids=checking_ids)
                state.last_signal_issue = current_period

        await asyncio.sleep(0.6)

# =========================
# AUTO SCHEDULER LOOP
# =========================
async def scheduler_loop(app: Application):
    """
    ✅ Auto schedule:
    - If now within window and bot not running -> auto start
    - If bot running AND started_by_schedule AND now outside -> auto stop
    """
    while True:
        try:
            now = datetime.now(BD_TZ)
            in_window = is_now_in_any_window(now)

            if state.auto_schedule_enabled:
                if in_window and (not state.running):
                    await start_session(app.bot, started_by_schedule=True)
                    app.create_task(engine_loop(app, state.session_id))
                elif (not in_window) and state.running and state.started_by_schedule:
                    await stop_session(app.bot, reason="schedule_end")

        except Exception as e:
            print("Scheduler error:", e)

        await asyncio.sleep(10)

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

    if data == "TOGGLE_AUTO":
        state.auto_schedule_enabled = not state.auto_schedule_enabled
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        return

    if data == "START:1M":
        # manual start -> scheduler won't auto-stop it
        if state.running:
            await stop_session(context.bot, reason="restart_manual")
        await start_session(context.bot, started_by_schedule=False)
        context.application.create_task(engine_loop(context.application, state.session_id))
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
# POST INIT (Render fix: start scheduler after event loop running)
# =========================
async def post_init(app: Application):
    # ✅ This runs when the event loop is running
    app.create_task(scheduler_loop(app))

# =========================
# MAIN
# =========================
def main():
    logging.basicConfig(level=logging.WARNING)
    keep_alive()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)  # ✅ FIX for "no running event loop"
        .build()
    )

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("panel", cmd_panel))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
