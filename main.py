import os
import time
import random
import asyncio
import logging
from dataclasses import dataclass, field
from threading import Thread
from typing import Dict, List, Optional, Set, Tuple

import requests
from flask import Flask
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================================================
#                CONFIG (PASTE ONLY TOKEN)
# =========================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8456002611:AAHZUGRB6VEPGwimGwpusCXuUSMS7yL2XTY")  # <-- paste or env
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "2222")  # optional

BRAND_NAME = os.getenv("BRAND_NAME", "⚡ TK MARUF OFFICIAL 24/7 SIGNAL")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/big_maruf_official0")

# Targets (3 channels)
TARGETS: Dict[str, int] = {
    "MAIN_GROUP": int(os.getenv("MAIN_GROUP_ID", "-1003263928753")),
    "VIP": int(os.getenv("VIP_ID", "-1002892329434")),
    "PUBLIC": int(os.getenv("PUBLIC_ID", "-1002629495753")),
}

# =========================================================
#                      STICKERS
# =========================================================
STICKERS = {
    # 1 min prediction
    "PRED_1M_BIG": "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    "PRED_1M_SMALL": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",

    # 30 sec prediction (SWAP as you requested)
    "PRED_30S_BIG": "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",   # swapped
    "PRED_30S_SMALL": "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE", # swapped

    # win stickers
    "WIN_BIG": "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    "WIN_SMALL": "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    "WIN_ANY_ALWAYS": "CAACAgUAAxkBAAEQUTZpdFC4094KaOEdiE3njwhAGVCuBAAC4hoAAt0EqVQXmdKVLGbGmzgE",

    # loss sticker
    "LOSS": "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",

    # extra random win stickers
    "WIN_RANDOM": [
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

    # color toggle stickers
    "COLOR_RED": "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    "COLOR_GREEN": "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",

    # start sticker always (but NOT on loss)
    "START_ALWAYS": "CAACAgUAAxkBAAEQTjRpcmWdzXBzA7e9KNz8QgTI6NXlxgACuRcAAh2x-FaJNjq4QG_DujgE",

    # session-start stickers by mode
    "START_30S": "CAACAgUAAxkBAAEQUrNpdYvDXIBff9O8TCRlI3QYJgfGiAAC1RQAAjGFMVfjtqxbDWbuEzgE",
    "START_1M": "CAACAgUAAxkBAAEQUrRpdYvESSIrn4-Lm936I6F8_BaN-wACChYAAuBHOVc6YQfcV-EKqjgE",

    # super win stickers 2-10
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
}

# =========================================================
#               KEEP ALIVE (Render 24/7)
# =========================================================
app = Flask("alive")

@app.get("/")
def _home():
    return f"{BRAND_NAME} is alive."

def _run_web():
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=_run_web, daemon=True).start()

# =========================================================
#               SAFE MARKET FEED (PLACEHOLDER)
# =========================================================
"""
NOTE:
এই জায়গায় তোমার data source বসবে।
আমি এখানে কোনো betting/lottery prediction automation দিচ্ছি না।
তবে bot non-stop চলবে, UI+stickers+cleanup+summary সব থাকবে।
"""

def fetch_market_snapshot(mode: str) -> Optional[dict]:
    """
    Return dict with:
      issueNumber: str
      number: int/str
    """
    now = int(time.time())
    issue = f"{now}"
    number = now % 10
    return {"issueNumber": issue, "number": number}

# =========================================================
#                   PREDICTION ENGINE
# =========================================================
class PredictionEngine:
    def __init__(self):
        self.history: List[str] = []          # BIG/SMALL newest first
        self.raw_history: List[dict] = []     # newest first
        self.last_prediction: Optional[str] = None

    def update_history(self, issue_data: dict):
        try:
            number = int(issue_data["number"])
            res = "BIG" if number >= 5 else "SMALL"
        except Exception:
            return

        # avoid duplicates by issueNumber
        if self.raw_history and self.raw_history[0].get("issueNumber") == issue_data.get("issueNumber"):
            return

        self.history.insert(0, res)
        self.raw_history.insert(0, issue_data)
        self.history = self.history[:60]
        self.raw_history = self.raw_history[:60]

    def get_pattern_signal(self, current_streak_loss: int):
        # (your provided logic)
        if len(self.history) < 15:
            return random.choice(["BIG", "SMALL"])

        h = self.history
        votes = []

        last_12 = h[:12]
        if last_12.count("BIG") > last_12.count("SMALL"):
            votes.append("BIG")
        else:
            votes.append("SMALL")

        votes.append(h[0])
        votes.append("SMALL" if h[0] == "BIG" else "BIG")

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
        match_big = match_small = 0
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

        votes.append(h[0])

        if current_streak_loss >= 2 and self.last_prediction:
            rec = "SMALL" if self.last_prediction == "BIG" else "BIG"
            votes.extend([rec, rec, rec])

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

# =========================================================
#                       BOT STATE
# =========================================================
@dataclass
class Stats:
    wins: int = 0
    losses: int = 0
    streak_win: int = 0
    streak_loss: int = 0
    max_streak_win: int = 0

@dataclass
class State:
    is_running: bool = False
    session_id: int = 0
    mode: str = "30S"
    engine: PredictionEngine = field(default_factory=PredictionEngine)
    authorized: Set[int] = field(default_factory=set)

    # channel selection
    selected_targets: Set[str] = field(default_factory=lambda: {"MAIN_GROUP"})

    # active bet
    active_bet: Optional[dict] = None
    last_period_processed: Optional[str] = None

    # stats
    stats: Stats = field(default_factory=Stats)

    # cleanup tracking
    checking_msgs: List[Tuple[int, int]] = field(default_factory=list)
    loss_msgs: List[Tuple[int, int]] = field(default_factory=list)

    # features
    color_on: bool = False

STATE = State()

# =========================================================
#                     UI (INLINE)
# =========================================================
def kb_main():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Start 30S", callback_data="start:30S"),
            InlineKeyboardButton("⚡ Start 1M", callback_data="start:1M"),
        ],
        [
            InlineKeyboardButton("🎯 Channel Select", callback_data="targets"),
            InlineKeyboardButton(("🟢 Color ON" if STATE.color_on else "⚪ Color OFF"), callback_data="color"),
        ],
        [
            InlineKeyboardButton("🛑 Stop + Summary", callback_data="stop"),
        ],
    ])

def kb_targets():
    rows = []
    for k in TARGETS:
        mark = "✅" if k in STATE.selected_targets else "⬜"
        rows.append([InlineKeyboardButton(f"{mark} {k}", callback_data=f"toggle:{k}")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="back")])
    return InlineKeyboardMarkup(rows)

# =========================================================
#                    FORMATTERS
# =========================================================
def _emoji_pick(pick: str) -> str:
    return "🟢" if pick == "BIG" else "🔴"

def fmt_signal(issue: str, pick: str) -> str:
    step = STATE.stats.streak_loss
    return (
        f"<b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Mode:</b> {STATE.mode}\n"
        f"🎲 <b>Period:</b> <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔮 <b>PREDICTION:</b> {_emoji_pick(pick)} <b>{pick}</b> {_emoji_pick(pick)}\n"
        f"🧠 <b>LossStep:</b> <b>{step}</b> / 8\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"➕ <a href='{CHANNEL_LINK}'><b>JOIN CHANNEL</b></a>"
    )

def fmt_checking(issue: str) -> str:
    return (
        f"🔎 <b>CHECKING...</b>\n"
        f"🎲 Period: <code>{issue}</code>\n"
        f"⏳ Result verifying..."
    )

def fmt_result(issue: str, res_num: int, res_type: str, pick: str, is_win: bool) -> str:
    if is_win:
        streak = STATE.stats.streak_win
        return (
            f"✅ <b>WIN CONFIRMED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎲 <b>Period:</b> <code>{issue}</code>\n"
            f"🎰 <b>Result:</b> <b>{res_num} ({res_type})</b>\n"
            f"🎯 <b>Pick:</b> <b>{pick}</b>\n"
            f"🏆 <b>Win Streak:</b> <b>{streak}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>{BRAND_NAME}</b>"
        )
    else:
        step = STATE.stats.streak_loss
        return (
            f"❌ <b>LOSS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎲 <b>Period:</b> <code>{issue}</code>\n"
            f"🎰 <b>Result:</b> <b>{res_num} ({res_type})</b>\n"
            f"🎯 <b>Pick:</b> <b>{pick}</b>\n"
            f"⚠️ <b>LOSS STEP:</b> <b>{step}</b> / 8\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>{BRAND_NAME}</b>"
        )

def fmt_summary() -> str:
    s = STATE.stats
    total = max(1, s.wins + s.losses)
    acc = int((s.wins / total) * 100)
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Report</b>\n"
        f"✅ Win: <b>{s.wins}</b>\n"
        f"❌ Loss: <b>{s.losses}</b>\n"
        f"🏆 Max Streak: <b>{s.max_streak_win}</b>\n"
        f"🎯 Accuracy: <b>{acc}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"🔗 <a href='{CHANNEL_LINK}'><b>REJOIN</b></a>"
    )

# =========================================================
#                 SEND HELPERS
# =========================================================
async def send_to_targets(context: ContextTypes.DEFAULT_TYPE, text: str, sticker: Optional[str] = None) -> None:
    for k in list(STATE.selected_targets):
        chat_id = TARGETS.get(k)
        if not chat_id:
            continue
        try:
            # Always sticker at start/end except loss rule applied by caller
            if sticker:
                await context.bot.send_sticker(chat_id, sticker)
            await context.bot.send_message(
                chat_id,
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logging.warning("Send failed to %s: %s", k, e)

async def send_checking(context: ContextTypes.DEFAULT_TYPE, issue: str) -> None:
    for k in list(STATE.selected_targets):
        chat_id = TARGETS.get(k)
        if not chat_id:
            continue
        try:
            msg = await context.bot.send_message(
                chat_id,
                fmt_checking(issue),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            STATE.checking_msgs.append((chat_id, msg.message_id))
        except Exception:
            pass

async def delete_checking(context: ContextTypes.DEFAULT_TYPE) -> None:
    items = STATE.checking_msgs[:]
    STATE.checking_msgs.clear()
    for chat_id, mid in items:
        try:
            await context.bot.delete_message(chat_id, mid)
        except Exception:
            pass

async def delete_loss_msgs(context: ContextTypes.DEFAULT_TYPE) -> None:
    items = STATE.loss_msgs[:]
    STATE.loss_msgs.clear()
    for chat_id, mid in items:
        try:
            await context.bot.delete_message(chat_id, mid)
        except Exception:
            pass

# =========================================================
#                  ENGINE LOOP
# =========================================================
async def engine_loop(context: ContextTypes.DEFAULT_TYPE, sid: int) -> None:
    """
    Non-stop loop with:
      - prediction sticker -> message -> checking -> result (stickers) -> delete checking
      - avoids duplicate periods
      - stop guard to prevent extra signal after summary
    """
    logging.info("Engine started sid=%s mode=%s", sid, STATE.mode)

    while STATE.is_running and STATE.session_id == sid:
        snap = await asyncio.to_thread(fetch_market_snapshot, STATE.mode)
        if not snap:
            await asyncio.sleep(0.7)
            continue

        issue = str(snap.get("issueNumber"))
        num = int(snap.get("number", 0))
        res_type = "BIG" if num >= 5 else "SMALL"

        # 1) handle feedback if active bet matched
        if STATE.active_bet and STATE.active_bet["period"] == issue:
            # prevent double processing
            if STATE.last_period_processed == issue:
                await asyncio.sleep(0.2)
                continue

            pick = STATE.active_bet["pick"]
            is_win = (pick == res_type)

            # update history
            STATE.engine.update_history(snap)

            # send result sticker+msg
            if is_win:
                STATE.stats.wins += 1
                STATE.stats.streak_win += 1
                STATE.stats.streak_loss = 0
                if STATE.stats.streak_win > STATE.stats.max_streak_win:
                    STATE.stats.max_streak_win = STATE.stats.streak_win

                # ALWAYS win sticker
                for k in list(STATE.selected_targets):
                    chat_id = TARGETS.get(k)
                    if not chat_id:
                        continue
                    try:
                        await context.bot.send_sticker(chat_id, STICKERS["WIN_ANY_ALWAYS"])
                    except Exception:
                        pass

                # super win 2-10
                sw = STATE.stats.streak_win
                if sw in STICKERS["SUPER_WIN"]:
                    sticker = STICKERS["SUPER_WIN"][sw]
                else:
                    # choose win type + random extra
                    sticker = STICKERS["WIN_BIG"] if res_type == "BIG" else STICKERS["WIN_SMALL"]
                await send_to_targets(context, fmt_result(issue, num, res_type, pick, True), sticker=sticker)

                # extra random sometimes
                if random.random() < 0.25:
                    try:
                        await send_to_targets(context, "🔥 <b>KEEP IT UP!</b>", sticker=random.choice(STICKERS["WIN_RANDOM"]))
                    except Exception:
                        pass

            else:
                STATE.stats.losses += 1
                STATE.stats.streak_loss += 1
                STATE.stats.streak_win = 0

                # loss sticker (NO start sticker here)
                await send_to_targets(context, fmt_result(issue, num, res_type, pick, False), sticker=STICKERS["LOSS"])

            # delete checking msg now
            await delete_checking(context)

            STATE.active_bet = None
            STATE.last_period_processed = issue

            await asyncio.sleep(0.2)
            continue

        # 2) send signal for NEXT period (simulate next by +1 on numeric issue if possible)
        if not STATE.active_bet:
            # compute "next issue"
            try:
                next_issue = str(int(issue) + 1)
            except Exception:
                next_issue = f"{issue}_NEXT"

            # avoid sending signal twice for same next_issue
            if STATE.last_period_processed == next_issue:
                await asyncio.sleep(0.25)
                continue

            # update history first
            STATE.engine.update_history(snap)

            pick = STATE.engine.get_pattern_signal(STATE.stats.streak_loss)

            # prediction sticker selection by mode
            if STATE.mode == "30S":
                pred_stk = STICKERS["PRED_30S_BIG"] if pick == "BIG" else STICKERS["PRED_30S_SMALL"]
            else:
                pred_stk = STICKERS["PRED_1M_BIG"] if pick == "BIG" else STICKERS["PRED_1M_SMALL"]

            # optional color sticker
            color_stk = None
            if STATE.color_on:
                color_stk = STICKERS["COLOR_GREEN"] if pick == "BIG" else STICKERS["COLOR_RED"]

            # send in exact order: pred sticker -> signal msg -> checking msg
            if color_stk:
                await send_to_targets(context, " ", sticker=color_stk)
            await send_to_targets(context, fmt_signal(next_issue, pick), sticker=pred_stk)
            await send_checking(context, next_issue)

            STATE.active_bet = {"period": next_issue, "pick": pick}

        await asyncio.sleep(0.6 if STATE.mode == "30S" else 1.2)

    logging.info("Engine exit sid=%s", sid)

# =========================================================
#                COMMANDS & CALLBACKS
# =========================================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in STATE.authorized:
        await update.message.reply_text("✅ <b>Unlocked</b>", parse_mode=ParseMode.HTML, reply_markup=kb_main())
    else:
        await update.message.reply_text("🔒 <b>Locked</b>\nSend password:", parse_mode=ParseMode.HTML)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = (update.message.text or "").strip()

    if uid not in STATE.authorized:
        if BOT_PASSWORD != "PASTE_PASSWORD_HERE" and msg == BOT_PASSWORD:
            STATE.authorized.add(uid)
            await update.message.reply_text("✅ <b>Access Granted</b>", parse_mode=ParseMode.HTML, reply_markup=kb_main())
        else:
            await update.message.reply_text("❌ Wrong password.", parse_mode=ParseMode.HTML)
        return

    await update.message.reply_text("Use menu 👇", reply_markup=kb_main())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""
    uid = q.from_user.id

    if uid not in STATE.authorized:
        await q.edit_message_text("🔒 Locked. Send password first.")
        return

    if data == "back":
        await q.edit_message_text("Menu:", reply_markup=kb_main())
        return

    if data == "targets":
        await q.edit_message_text("🎯 Select Targets:", reply_markup=kb_targets())
        return

    if data.startswith("toggle:"):
        key = data.split(":", 1)[1]
        if key in TARGETS:
            if key in STATE.selected_targets:
                STATE.selected_targets.remove(key)
            else:
                STATE.selected_targets.add(key)
        await q.edit_message_text("🎯 Select Targets:", reply_markup=kb_targets())
        return

    if data == "color":
        STATE.color_on = not STATE.color_on
        await q.edit_message_text("Menu:", reply_markup=kb_main())
        return

    if data.startswith("start:"):
        mode = data.split(":", 1)[1]
        if mode not in ("30S", "1M"):
            return

        # stop previous session safely
        STATE.session_id += 1
        STATE.is_running = False
        await delete_checking(context)
        await delete_loss_msgs(context)
        await asyncio.sleep(0.2)

        # reset stats & start
        STATE.mode = mode
        STATE.is_running = True
        STATE.stats = Stats()
        STATE.engine = PredictionEngine()
        STATE.active_bet = None
        STATE.last_period_processed = None
        sid = STATE.session_id

        # start stickers by mode + always sticker
        start_stk = STICKERS["START_30S"] if mode == "30S" else STICKERS["START_1M"]
        await send_to_targets(context, "✅ <b>SESSION STARTED</b>", sticker=start_stk)
        await send_to_targets(context, " ", sticker=STICKERS["START_ALWAYS"])

        await q.edit_message_text(
            f"✅ Started <b>{mode}</b>\nTargets: <b>{', '.join(sorted(STATE.selected_targets))}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_main(),
        )

        context.application.create_task(engine_loop(context, sid))
        return

    if data == "stop":
        # stop guard first
        STATE.session_id += 1
        STATE.is_running = False

        await delete_checking(context)
        await delete_loss_msgs(context)

        # summary must go to groups
        await send_to_targets(context, fmt_summary())

        await q.edit_message_text("🛑 Stopped + Summary Sent.", reply_markup=kb_main())
        return

# =========================================================
#                       MAIN
# =========================================================
def main():
    logging.basicConfig(level=logging.INFO)

    if not BOT_TOKEN or BOT_TOKEN == "PASTE_TOKEN_HERE" or ":" not in BOT_TOKEN:
        raise RuntimeError("Invalid BOT_TOKEN. Paste your token or set BOT_TOKEN env var.")

    keep_alive()

    app_tg = Application.builder().token(BOT_TOKEN).build()
    app_tg.add_handler(CommandHandler("start", cmd_start))
    app_tg.add_handler(CallbackQueryHandler(on_callback))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app_tg.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
