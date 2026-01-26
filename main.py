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
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

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
API_PAGE_SIZE = 60               # ✅ 30S এর জন্য বড় list
PENDING_TTL_SECONDS_30S = 180    # ✅ 3 মিনিটে না পেলে auto-drop
PENDING_TTL_SECONDS_1M = 360


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

        if (not self.raw_history) or (str(self.raw_history[0].get("issueNumber")) != str(issue_data.get("issueNumber"))):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:120]
            self.raw_history = self.raw_history[:120]

    def get_pattern_signal(self, streak_loss: int) -> str:
        if not self.raw_history:
            return random.choice(["BIG", "SMALL"])
        try:
            last_num = int(self.raw_history[0]["number"])
            pred = "BIG" if (last_num + 1) % 2 == 0 else "SMALL"
            if streak_loss >= 2 and self.history:
                pred = self.history[0]
            return pred
        except Exception:
            return random.choice(["BIG", "SMALL"])

    def calc_confidence(self, streak_loss: int) -> int:
        base = random.randint(88, 95)
        if streak_loss >= 1:
            base -= 5
        return base


# =========================
# BOT STATE
# =========================
def now_bd_str() -> str:
    return datetime.now(BD_TZ).strftime("%H:%M:%S")

def mode_label(mode: str) -> str:
    return "30 SEC" if mode == "30S" else "1 MIN"

@dataclass
class PendingBet:
    issue: str
    pick: str
    created_at: float = field(default_factory=lambda: time.time())
    checking_msg_ids: Dict[int, int] = field(default_factory=dict)

@dataclass
class BotState:
    running: bool = False
    mode: str = "30S"
    session_id: int = 0
    engine: PredictionEngine = field(default_factory=PredictionEngine)

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

    # ✅ IMPORTANT FIX
    last_sent_issue_num: Optional[int] = None   # sequential period
    last_signal_issue: Optional[str] = None
    pending: Dict[str, PendingBet] = field(default_factory=dict)  # key=issue

state = BotState()


# =========================
# FETCH LIST
# =========================
def _fetch_list_sync(mode: str) -> List[dict]:
    type_id = 5 if mode == "30S" else 1
    payload = {
        "pageSize": API_PAGE_SIZE,
        "pageNo": 1,
        "typeId": type_id,
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
            lst = (((data or {}).get("data") or {}).get("list")) or []
            return lst if isinstance(lst, list) else []
    except Exception:
        pass
    return []

async def fetch_list(mode: str) -> List[dict]:
    return await asyncio.to_thread(_fetch_list_sync, mode)


# =========================
# MESSAGE FORMATTERS
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
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>PREDICTION</b> ➜ {pick_txt}\n"
        f"🔥 <b>Confidence</b> ➜ <b>{conf}%</b>\n"
        f"🧠 <b>Recovery</b> ➜ <b>{recovery_label(state.streak_loss)}</b>\n"
        f"⏱ <b>BD Time</b> ➜ <b>{now_bd_str()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>REGISTER:</b> <a href='{REG_LINK}'>CLICK HERE</a>"
    )

def format_checking(wait_issue: str) -> str:
    return (
        f"🛰 <b>CHECKING RESULT...</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"🧾 <b>Waiting:</b> <code>{wait_issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <i>Syncing result from server...</i>"
    )

def format_result(issue: str, res_num: str, res_type: str, pick: str, is_win: bool) -> str:
    pick_txt, _ = pretty_pick(pick)
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    color_result = "GREEN" if res_type == "BIG" else "RED"

    promo_text = ""
    if is_win:
        header = "✅ <b>WIN CONFIRMED</b> ✅"
        extra = f"\n🎨 <b>Color Win:</b> <b>{color_result}</b>" if state.color_mode else ""
        promo_text = (
            f"\n💎 <b>PREMIUM INFO</b> 💎\n"
            f"🚀 <i>Aro top working file er jonno ekhane\n"
            f"account khule amar inbox e knock din!</i>\n"
            f"👤 <b>Owner:</b> {OWNER_USERNAME}"
        )
    else:
        header = "❌ <b>LOSS CONFIRMED</b> ❌"
        extra = ""

    return (
        f"{header}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{res_num} ({res_type})</b>\n"
        f"🎯 <b>Your Pick:</b> {pick_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 <b>Recovery:</b> <b>{recovery_label(state.streak_loss)}</b>\n"
        f"{extra}\n"
        f"📊 <b>W:</b> <b>{state.wins}</b> | <b>L:</b> <b>{state.losses}</b> | ⏱ <b>{now_bd_str()}</b>"
        f"{promo_text}"
    ).strip()

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
        f"🔥 <b>Max Win Streak:</b> <b>{state.max_win_streak}</b>\n"
        f"🧨 <b>Max Loss Streak:</b> <b>{state.max_loss_streak}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Closed:</b> <b>{now_bd_str()}</b>\n"
        f"🔗 <b>JOIN VIP:</b> <a href='{CHANNEL_LINK}'>CLICK HERE</a>"
    )


# =========================
# PANEL UI
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
    color = "🎨 <b>COLOR:</b> <b>ON</b>" if state.color_mode else "🎨 <b>COLOR:</b> <b>OFF</b>"
    grace = "🧠 <b>STOP AFTER RECOVER:</b> ✅" if state.graceful_stop_requested else "🧠 <b>STOP AFTER RECOVER:</b> ❌"

    return (
        "🔐 <b>CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Status:</b> {running}\n"
        f"⚡ <b>Mode:</b> <b>{mode_label(state.mode)}</b>\n"
        f"{color}\n"
        f"{grace}\n"
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

    # delete all checking messages
    for pb in list(state.pending.values()):
        for cid, mid in pb.checking_msg_ids.items():
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
    state.graceful_stop_requested = False
    state.pending.clear()
    state.last_sent_issue_num = None
    state.last_signal_issue = None

async def start_session(bot, mode: str):
    state.mode = mode
    state.session_id += 1
    state.running = True
    state.stop_event.clear()
    state.graceful_stop_requested = False
    state.engine = PredictionEngine()
    reset_stats()

    state.pending.clear()
    state.last_sent_issue_num = None
    state.last_signal_issue = None

    stk = STICKERS["START_30S"] if mode == "30S" else STICKERS["START_1M"]
    await broadcast_sticker(bot, stk)


# =========================
# ENGINE LOOP (FINAL FIX)
# =========================
def _issue_num(x) -> Optional[int]:
    try:
        return int(str(x))
    except Exception:
        return None

def _res_type(entry: dict) -> str:
    try:
        return "BIG" if int(entry.get("number", 0)) >= 5 else "SMALL"
    except Exception:
        return "SMALL"

async def engine_loop(context: ContextTypes.DEFAULT_TYPE, my_session: int):
    bot = context.bot

    while state.running and state.session_id == my_session:
        if state.stop_event.is_set():
            break

        now = datetime.now(BD_TZ)
        sec = now.second

        # Safe window
        if state.mode == "1M":
            is_safe_time = (sec <= 50)
        else:
            is_safe_time = ((sec % 30) <= 20)

        lst = await fetch_list(state.mode)

        # seed last_sent_issue_num from API (only once)
        if state.last_sent_issue_num is None:
            if lst:
                li = _issue_num(lst[0].get("issueNumber"))
                if li is not None:
                    state.last_sent_issue_num = li
            # if still none, just wait a bit
            if state.last_sent_issue_num is None:
                await asyncio.sleep(0.8)
                continue

        # update history from latest
        if lst:
            state.engine.update_history(lst[0])

        # build map for fast exact match
        result_map = {str(it.get("issueNumber")): it for it in lst if it.get("issueNumber") is not None}

        # 1) resolve pending EXACT only
        resolved = []
        for issue, pb in list(state.pending.items()):
            hit = result_map.get(issue)
            if hit:
                res_num = str(hit.get("number"))
                res_type = _res_type(hit)
                pick = pb.pick
                is_win = (pick == res_type)

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
                    await broadcast_sticker(bot, STICKERS["WIN_BIG"] if res_type == "BIG" else STICKERS["WIN_SMALL"])
                    await broadcast_sticker(bot, STICKERS["WIN_ANY"])
                else:
                    state.losses += 1
                    state.streak_loss += 1
                    state.streak_win = 0
                    state.max_loss_streak = max(state.max_loss_streak, state.streak_loss)
                    await broadcast_sticker(bot, STICKERS["LOSS"])

                await broadcast_message(bot, format_result(issue, res_num, res_type, pick, is_win))

                for cid, mid in pb.checking_msg_ids.items():
                    await safe_delete(bot, cid, mid)

                resolved.append(issue)

                if state.graceful_stop_requested and is_win:
                    await stop_session(bot, reason="graceful_done")
                    return

        for issue in resolved:
            state.pending.pop(issue, None)

        # 2) TTL drop (no freeze)
        ttl = PENDING_TTL_SECONDS_1M if state.mode == "1M" else PENDING_TTL_SECONDS_30S
        for issue, pb in list(state.pending.items()):
            if (time.time() - pb.created_at) > ttl:
                for cid, mid in pb.checking_msg_ids.items():
                    await safe_delete(bot, cid, mid)
                state.pending.pop(issue, None)

        # 3) send next signal sequentially (NO SKIP)
        if is_safe_time:
            next_issue_num = state.last_sent_issue_num + 1
            next_issue = str(next_issue_num)

            # prevent duplicate in same period
            if state.last_signal_issue != next_issue and next_issue not in state.pending:

                if state.streak_loss >= MAX_RECOVERY_STEPS:
                    await broadcast_message(bot, "🧊 <b>SAFETY STOP</b>")
                    await stop_session(bot, reason="max_steps")
                    return

                pred = state.engine.get_pattern_signal(state.streak_loss)
                conf = state.engine.calc_confidence(state.streak_loss)

                if state.mode == "30S":
                    s_stk = STICKERS["PRED_30S_BIG"] if pred == "BIG" else STICKERS["PRED_30S_SMALL"]
                else:
                    s_stk = STICKERS["PRED_1M_BIG"] if pred == "BIG" else STICKERS["PRED_1M_SMALL"]

                await broadcast_sticker(bot, s_stk)
                if state.color_mode:
                    await broadcast_sticker(bot, STICKERS["COLOR_GREEN"] if pred == "BIG" else STICKERS["COLOR_RED"])

                await broadcast_message(bot, format_signal(next_issue, pred, conf))

                checking_ids = {}
                for cid in state.selected_targets:
                    try:
                        m = await bot.send_message(cid, format_checking(next_issue), parse_mode=ParseMode.HTML)
                        checking_ids[cid] = m.message_id
                    except Exception:
                        pass

                state.pending[next_issue] = PendingBet(issue=next_issue, pick=pred, checking_msg_ids=checking_ids)
                state.last_signal_issue = next_issue
                state.last_sent_issue_num = next_issue_num  # ✅ crucial: sequential

        await asyncio.sleep(0.5)


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
            if state.streak_loss == 0 and not state.pending:
                await stop_session(context.bot, reason="graceful_now")
        await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=selector_markup())
        return


# =========================
# MAIN
# =========================
def main():
    logging.basicConfig(level=logging.WARNING)

    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN missing! Set environment variable BOT_TOKEN.")

    keep_alive()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("panel", cmd_panel))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
