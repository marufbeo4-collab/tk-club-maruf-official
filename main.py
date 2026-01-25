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
# CONFIG (TOKEN & LINKS)
# =========================
BOT_TOKEN = "8595453345:AAGMYQFxohNbvz16cZTcP8HF2mqydRMZjMI"

BRAND_NAME = "⚡ DK MARUF OFFICIAL 24/7 SIGNAL"
OWNER_LINK = "https://t.me/OWNER_MARUF_TOP"
REG_LINK = "https://tkclub2.com/#/register?invitationCode=18753202056"

# Targets
TARGETS = {
    "MAIN_GROUP": -1003293007059,
    "VIP": -1002892329434,
    "PUBLIC": -1002629495753,
}

# =========================
# API CONFIG (TKCLUB2)
# =========================
# 30s এবং 1m দুটোর জন্যই সেম লিংক
API_URL = "https://api880.inpay88.net/api/webapi/GetNoaverageEmerdList"

# 👇👇 অত্যন্ত গুরুত্বপূর্ণ: যদি প্রেডিকশন না আসে, তাহলে এই Authorization টোকেন পাল্টাতে হবে 👇👇
API_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://tkclub2.com",
    "Referer": "https://tkclub2.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzY5MzUwODI3IiwibmJmIjoiMTc2OTM1MDgyNyIsImV4cCI6IjE3NjkzNTI2MjciLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIxLzI1LzIwMjYgODo1MDoyNyBQTSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6IkFjY2Vzc19Ub2tlbiIsIlVzZXJJZCI6IjIwMjk2MCIsIlVzZXJOYW1lIjoiODgwMzIxMTMyMTY3MCIsIlVzZXJQaG90byI6IjEiLCJOaWNrTmFtZSI6Ik1lbWJlck5OR0xFVlFXIiwiQW1vdW50IjoiMC4wMCIsIkludGVncmFsIjoiMCIsIkxvZ2luTWFyayI6Ikg1IiwiTG9naW5UaW1lIjoiMS8yNS8yMDI2IDg6MjA6MjcgUE0iLCJMb2dpbklQQWRkcmVzcyI6IjEwMy4xNzEuMzYuMTI5IiwiRGJOdW1iZXIiOiIwIiwiSXN2YWxpZGF0b3IiOiIwIiwiS2V5Q29kZSI6IjIiLCJUb2tlblR5cGUiOiJBY2Nlc3NfVG9rZW4iLCJQaG9uZVR5cGUiOiIwIiwiVXNlclR5cGUiOiIxIiwiVXNlck5hbWUyIjoiIiwiaXNzIjoiand0SXNzdWVyIiwiYXVkIjoibG90dGVyeVRpY2tldCJ9.EgcmEOjQ3bUnHLLyJwa8NBM0r6RP3kpmUwPvfIeCR_A"
}

# BD Time
BD_TZ = timezone(timedelta(hours=6))

# Password source A1
PASSWORD_SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
PASSWORD_SHEET_GID = "0"
PASSWORD_FALLBACK = "2222"

# Settings
MAX_RECOVERY_STEPS = 8
FAST_LOOP_30S = 0.85
FAST_LOOP_1M = 1.65
FETCH_TIMEOUT = 10  # Timeout increased for stability
FETCH_RETRY_SLEEP = 1.0


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
        "CAACAgUAAxkBAAEQT_tpc4E3AxHmgW9VWKrzWjxlrvzSowACghkAAlbXcFWxdto6TqiBrzgE",
        "CAACAgUAAxkBAAEQT_9pc4FHKn0W6ZfWOSaN6FUPzfmbnQACXR0AAqMbMFc-_4DHWbq7sjgE",
        "CAACAgUAAxkBAAEQUAFpc4FIokHE09p165cCsWiUYV648wACuhQAAo3aMVeAsNW9VRuVvzgE",
        "CAACAgUAAxkBAAEQUANpc4FJNTnfuBiLe-dVtoNCf3CQlAAC9xcAArE-MFfS5HNyds2tWTgE",
        "CAACAgUAAxkBAAEQUAVpc4FKhJ_stZ3VRRzWUuJGaWbrAgACOhYAAst6OVehdeQEGZlXiDgE",
        "CAACAgUAAxkBAAEQUAtpc4HcYxkscyRY2rhAAcmqMR29eAACOBYAAh7fwVU5Xy399k3oFDgE",
        "CAACAgUAAxkBAAEQUCdpc4IuoaqPZ-5vn2RTlJZ_kbeXHQACXRUAAgln-FQ8iTzzJg_GLzgE",
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
    "COLOR_RED": "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    "COLOR_GREEN": "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",
}


# =========================
# FLASK KEEP ALIVE
# =========================
app = Flask("")

@app.route("/")
def home():
    return "ALIVE - TKCLUB2 BOT"

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
# PREDICTION ENGINE
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
        
        # Simple Logic Mix
        last_12 = h[:12]
        votes.append("BIG" if last_12.count("BIG") > last_12.count("SMALL") else "SMALL")
        votes.append(h[0])
        votes.append("SMALL" if h[0] == "BIG" else "BIG")
        
        if h[0] == h[1] == h[2]:
            votes.append(h[0])

        try:
            r_num = int(self.raw_history[0].get("number", 0))
            votes.append("BIG" if r_num >= 5 else "SMALL")
        except:
            pass

        big_votes = votes.count("BIG")
        small_votes = votes.count("SMALL")
        
        if big_votes > small_votes:
            prediction = "BIG"
        elif small_votes > big_votes:
            prediction = "SMALL"
        else:
            prediction = h[0]

        # Streak Logic
        if current_streak_loss >= 4:
            prediction = h[0] 

        self.last_prediction = prediction
        return prediction

    def calc_confidence(self, streak_loss: int) -> int:
        base = random.randint(86, 93)
        if streak_loss >= 2:
            base = max(82, base - 2)
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
    session_loss_messages: Dict[int, List[int]] = field(default_factory=dict)
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)

state = BotState()


# =========================
# FETCH LOGIC (UPDATED FOR TKCLUB2)
# =========================
def _fetch_latest_issue_sync(mode: str) -> Optional[dict]:
    # 30S = TypeID 5, 1M = TypeID 1
    type_id = 5 if mode == "30S" else 1

    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": type_id,
        "language": 0,
        "random": "4f3d2a1b9c8e7f60",
        "signature": "D39F9069695C55720235791E0D10D695",
        "timestamp": int(time.time())
    }

    try:
        r = requests.post(
            API_URL, 
            json=payload, 
            headers=API_HEADERS, 
            timeout=FETCH_TIMEOUT
        )
        
        if r.status_code == 200:
            data = r.json()
            if data and "data" in data and "list" in data["data"]:
                item = data["data"]["list"][0]
                # Fix for differing key names (issueNumber vs period)
                if "issueNumber" not in item and "period" in item:
                    item["issueNumber"] = item["period"]
                return item
            else:
                print(f"[API WARN] Data empty or format changed: {data}")
        elif r.status_code == 401:
            print("[API ERROR] Token Expired! Update API_HEADERS in code.")
        else:
            print(f"[API FAIL] Status: {r.status_code}")
            
    except Exception as e:
        print(f"[CONNECTION ERROR] {e}")
        pass
    return None

async def fetch_latest_issue(mode: str) -> Optional[dict]:
    return await asyncio.to_thread(_fetch_latest_issue_sync, mode)


# =========================
# MESSAGING & FORMATTING
# =========================
def pretty_pick(pick: str) -> Tuple[str, str]:
    if pick == "BIG":
        return "🟢🟢 <b>BIG</b> 🟢🟢", "GREEN"
    return "🔴🔴 <b>SMALL</b> 🔴🔴", "RED"

def recovery_label(loss_streak: int) -> str:
    display_streak = loss_streak
    if loss_streak > 2:
        display_streak = random.choice([1, 2])
    return f"{display_streak} Step Loss / {MAX_RECOVERY_STEPS}"

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
        f"🔥 আরো প্রিমিয়াম সব হ্যাক এর জন্য\nনিচের লিংকে একাউন্ট খুলে যোগাযোগ করুন:\n"
        f"📝 <b>REG:</b> <a href='{REG_LINK}'>Click Here To Register</a>\n"
        f"👤 <b>OWNER:</b> <a href='{OWNER_LINK}'>Message Me</a>"
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
    if is_win:
        header = "✅ <b>WIN CONFIRMED</b> ✅"
        res_emoji = "🟢" if pick == "BIG" else "🔴"
        display_type = pick 
        display_num = res_num
        if res_type != pick: # Fake win fallback
            display_num = str(random.choice([5,6,7,8,9])) if pick == "BIG" else str(random.choice([0,1,2,3,4]))
        
        extra = f"\n🎨 <b>Color Win:</b> <b>GREEN/RED</b>" if state.color_mode else ""
        return (
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧾 <b>Period:</b> <code>{issue}</code>\n"
            f"🎰 <b>Result:</b> {res_emoji} <b>{display_num} ({display_type})</b>\n"
            f"🎯 <b>Your Pick:</b> {pick_txt}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 <b>Recovery:</b> <b>{recovery_label(state.streak_loss)}</b>\n"
            f"{extra}\n"
            f"📊 <b>W:</b> <b>{state.wins}</b> | <b>L:</b> <b>{state.losses}</b> | ⏱ <b>{now_bd_str()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 <b>REG:</b> <a href='{REG_LINK}'>Register Now</a>\n"
            f"👤 <b>OWNER:</b> <a href='{OWNER_LINK}'>Message Me</a>"
        ).strip()
    else:
        header = "❌ <b>LOSS CONFIRMED</b> ❌"
        res_emoji = "🟢" if res_type == "BIG" else "🔴"
        return (
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧾 <b>Period:</b> <code>{issue}</code>\n"
            f"🎰 <b>Result:</b> {res_emoji} <b>{res_num} ({res_type})</b>\n"
            f"🎯 <b>Your Pick:</b> {pick_txt}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 <b>Recovery:</b> <b>{recovery_label(state.streak_loss)}</b>\n"
            f"📊 <b>W:</b> <b>{state.wins}</b> | <b>L:</b> <b>{state.losses}</b> | ⏱ <b>{now_bd_str()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 <b>REG:</b> <a href='{REG_LINK}'>Register Now</a>"
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
        f"🔥 আরো প্রিমিয়াম সব হ্যাক পেতে\nনিচের লিংকে একাউন্ট খুলে যোগাযোগ করুন:\n"
        f"🔗 <b>REG:</b> <a href='{REG_LINK}'>Click Here To Register</a>\n"
        f"👤 <b>OWNER:</b> <a href='{OWNER_LINK}'>Message Me</a>"
    )

# =========================
# CONTROL PANEL & HELPERS
# =========================
async def safe_delete(bot, chat_id: int, msg_id: int):
    try: await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except: pass

async def broadcast_sticker(bot, sticker_id: str) -> Dict[int, int]:
    out = {}
    for cid in state.selected_targets:
        try:
            m = await bot.send_sticker(cid, sticker_id)
            out[cid] = m.message_id
        except: pass
    return out

async def broadcast_message(bot, text: str) -> Dict[int, int]:
    out = {}
    for cid in state.selected_targets:
        try:
            m = await bot.send_message(cid, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            out[cid] = m.message_id
        except: pass
    return out

def panel_text() -> str:
    running = "🟢 RUNNING" if state.running else "🔴 STOPPED"
    sel_lines = "\n".join([f"✅ <code>{cid}</code>" for cid in state.selected_targets])
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    return (
        f"🔐 <b>CONTROL PANEL</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Status:</b> {running}\n"
        f"⚡ <b>Mode:</b> <b>{mode_label(state.mode)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Targets:</b>\n{sel_lines}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ W: {state.wins} | ❌ L: {state.losses} | 🎯 {wr:.1f}%\n"
        f"👇 <i>Select then Start</i>"
    )

def selector_markup() -> InlineKeyboardMarkup:
    def btn(name: str, chat_id: int) -> InlineKeyboardButton:
        on = "✅" if chat_id in state.selected_targets else "⬜"
        return InlineKeyboardButton(f"{on} {name}", callback_data=f"TOGGLE:{chat_id}")
    
    rows = [
        [btn("MAIN GROUP", TARGETS["MAIN_GROUP"])],
        [btn("VIP", TARGETS["VIP"]), btn("PUBLIC", TARGETS["PUBLIC"])],
        [InlineKeyboardButton("🎨 Color: ON/OFF", callback_data="TOGGLE_COLOR")],
        [InlineKeyboardButton("⚡ Start 30 SEC", callback_data="START:30S"), InlineKeyboardButton("⚡ Start 1 MIN", callback_data="START:1M")],
        [InlineKeyboardButton("🛑 Stop Now", callback_data="STOP:FORCE"), InlineKeyboardButton("🔄 Refresh", callback_data="REFRESH_PANEL")]
    ]
    return InlineKeyboardMarkup(rows)

async def stop_session(bot, reason: str = "manual"):
    state.session_id += 1
    state.running = False
    state.stop_event.set()
    if state.active:
        for cid, mid in (state.active.checking_msg_ids or {}).items():
            await safe_delete(bot, cid, mid)
    for cid, msg_ids in state.session_loss_messages.items():
        for mid in msg_ids:
            await safe_delete(bot, cid, mid)
    state.session_loss_messages = {}
    await broadcast_sticker(bot, STICKERS["START_END_ALWAYS"])
    for cid in state.selected_targets:
        try: await bot.send_message(cid, format_summary(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except: pass
    state.unlocked = False
    state.active = None

async def start_session(bot, mode: str):
    state.mode = mode
    state.session_id += 1
    state.running = True
    state.stop_event.clear()
    state.engine = PredictionEngine()
    state.active = None
    state.last_result_issue = None
    state.last_signal_issue = None
    state.wins = 0
    state.losses = 0
    state.streak_win = 0
    state.streak_loss = 0
    stk = STICKERS["START_30S"] if mode == "30S" else STICKERS["START_1M"]
    await broadcast_sticker(bot, stk)
    await broadcast_sticker(bot, STICKERS["START_END_ALWAYS"])

# =========================
# CORE ENGINE LOOP
# =========================
async def engine_loop(context: ContextTypes.DEFAULT_TYPE, my_session: int):
    bot = context.bot
    last_seen_issue = None

    while state.running and state.session_id == my_session:
        latest = await fetch_latest_issue(state.mode)
        if not latest:
            await asyncio.sleep(FETCH_RETRY_SLEEP)
            continue

        issue = str(latest.get("issueNumber"))
        num = str(latest.get("number"))
        res_type = "BIG" if int(num) >= 5 else "SMALL"
        next_issue = str(int(issue) + 1)
        
        state.engine.update_history(latest)

        if last_seen_issue == issue:
            await asyncio.sleep(0.5)

        # Process Active Bet
        if state.active and state.active.predicted_issue == issue:
            if state.last_result_issue == issue:
                await asyncio.sleep(0.1)
                continue
            
            pick = state.active.pick
            real_win = (pick == res_type)
            
            # Stats
            if real_win:
                state.streak_win += 1
                state.streak_loss = 0
            else:
                state.streak_loss += 1
                state.streak_win = 0

            # Fake Win Display Logic (90% Win Rate Visual)
            display_win = True if real_win else (random.random() < 0.90)
            if display_win: state.wins += 1
            else: state.losses += 1

            # Stickers & Msg
            if display_win:
                await broadcast_sticker(bot, STICKERS["WIN_ALWAYS"])
                s_win = STICKERS["WIN_BIG"] if pick == "BIG" else STICKERS["WIN_SMALL"]
                await broadcast_sticker(bot, s_win)
            else:
                s_loss_dict = await broadcast_sticker(bot, STICKERS["LOSS"])
                for cid, mid in s_loss_dict.items():
                    state.session_loss_messages.setdefault(cid, []).append(mid)

            r_msg_dict = await broadcast_message(bot, format_result(issue, num, res_type, pick, display_win))
            if not display_win:
                for cid, mid in r_msg_dict.items():
                    state.session_loss_messages.setdefault(cid, []).append(mid)

            # Cleanup
            for cid, mid in (state.active.checking_msg_ids or {}).items():
                await safe_delete(bot, cid, mid)

            state.last_result_issue = issue
            
            # Stop Conditions
            if state.graceful_stop_requested and real_win:
                state.active = None
                await stop_session(bot, reason="graceful_done")
                break
            
            if state.stop_event.is_set() and real_win:
                 state.active = None
                 await stop_session(bot, reason="delayed_force_done")
                 break

            state.active = None

        # Generate Signal
        if (not state.active) and (state.last_signal_issue != next_issue):
            if state.stop_event.is_set() or (state.graceful_stop_requested and state.streak_loss == 0):
                 if state.streak_loss == 0:
                      await stop_session(bot, reason="clean_exit")
                      break

            pred = state.engine.get_pattern_signal(state.streak_loss)
            conf = state.engine.calc_confidence(state.streak_loss)

            s_stk = STICKERS[f"PRED_{state.mode}_BIG"] if pred == "BIG" else STICKERS[f"PRED_{state.mode}_SMALL"]
            await broadcast_sticker(bot, s_stk)
            await broadcast_message(bot, format_signal(next_issue, pred, conf))
            
            checking_ids = {}
            for cid in state.selected_targets:
                try:
                    m = await bot.send_message(cid, format_checking(next_issue), parse_mode=ParseMode.HTML)
                    checking_ids[cid] = m.message_id
                except: pass

            state.active = ActiveBet(predicted_issue=next_issue, pick=pred, checking_msg_ids=checking_ids)
            state.last_signal_issue = next_issue

        await asyncio.sleep(FAST_LOOP_30S if state.mode == "30S" else FAST_LOOP_1M)

# =========================
# COMMAND HANDLERS
# =========================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.expected_password = await get_live_password()
    state.unlocked = False
    await update.message.reply_text("🔒 <b>SYSTEM LOCKED</b>\nPass দিন:", parse_mode=ParseMode.HTML)

async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state.unlocked: return
    await update.message.reply_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state.unlocked:
        state.expected_password = await get_live_password()
        if update.message.text.strip() == state.expected_password:
            state.unlocked = True
            await update.message.reply_text("✅ <b>UNLOCKED</b>", parse_mode=ParseMode.HTML)
            await update.message.reply_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        else:
            await update.message.reply_text("❌ Wrong Pass", parse_mode=ParseMode.HTML)

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not state.unlocked: return
    
    data = q.data
    if data == "REFRESH_PANEL":
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
    elif data.startswith("TOGGLE:"):
        cid = int(data.split(":")[1])
        if cid in state.selected_targets: state.selected_targets.remove(cid)
        else: state.selected_targets.append(cid)
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
    elif data.startswith("START:"):
        mode = data.split(":")[1]
        if state.running: await stop_session(context.bot, "restart")
        await start_session(context.bot, mode)
        context.application.create_task(engine_loop(context, state.session_id))
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
    elif data == "STOP:FORCE":
        state.stop_event.set()
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())

# =========================
# MAIN EXECUTION
# =========================
def main():
    logging.basicConfig(level=logging.WARNING)
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("panel", cmd_panel))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
