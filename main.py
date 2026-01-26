import os
import time
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
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# =========================
# CONFIG (PASTE HERE)
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8456002611:AAHZUGRB6VEPGwimGwpusCXuUSMS7yL2XTY")  # <-- Render env recommended
BRAND_NAME = os.getenv("BRAND_NAME", "⚡ TK MARUF OFFICIAL 24/7 SIGNAL")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/big_maruf_official0")

# Targets (you can edit / add more)
TARGETS: Dict[str, int] = {
    "MAIN_GROUP": int(os.getenv("MAIN_GROUP_ID", "-1003263928753")),
    "VIP": int(os.getenv("VIP_ID", "-1002892329434")),
    "PUBLIC": int(os.getenv("PUBLIC_ID", "-1002629495753")),
}

# Simple password lock (keep it in env in production)
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "PASTE_PASSWORD_HERE")

# =========================
# BASIC WEB KEEP-ALIVE
# =========================
app = Flask("alive")

@app.get("/")
def home():
    return f"{BRAND_NAME} is alive."

def _run_web():
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=_run_web, daemon=True)
    t.start()

# =========================
# SAFE PLACEHOLDER API LAYER
# =========================
"""
⚠️ IMPORTANT:
- This bot skeleton does NOT include any betting/lottery prediction automation.
- Replace fetch_market_snapshot() with your own LEGIT / PUBLIC data source if needed.
- Do NOT paste private bearer tokens here. Use Render env vars if you must.
"""

def fetch_market_snapshot(mode: str) -> Tuple[Optional[dict], str]:
    """
    Placeholder data source.
    Return (data, status). data should be dict containing:
      - "issueNumber" : str
      - "number"      : str or int
    """
    # Example "fake" snapshot to keep system running without external API:
    # You can remove and replace with your own allowed API call.
    now = int(time.time())
    issue = f"{now}"
    number = str(now % 10)
    return {"issueNumber": issue, "number": number}, "OK"

# =========================
# STATE
# =========================
@dataclass
class SessionStats:
    wins: int = 0
    losses: int = 0
    streak_win: int = 0
    streak_loss: int = 0
    max_streak_win: int = 0

@dataclass
class BotState:
    is_running: bool = False
    session_id: int = 0
    mode: str = "30S"  # "30S" or "1M"
    authorized: Set[int] = field(default_factory=set)
    selected_targets: Set[str] = field(default_factory=lambda: {"MAIN_GROUP"})
    stats: SessionStats = field(default_factory=SessionStats)

    # message tracking for cleanup
    checking_msg_ids: List[Tuple[int, int]] = field(default_factory=list)  # (chat_id, msg_id)
    loss_msg_ids: List[Tuple[int, int]] = field(default_factory=list)

STATE = BotState()

# =========================
# UI HELPERS
# =========================
def kbd_main() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("⚡ Start 30 Seconds", callback_data="start:30S"),
         InlineKeyboardButton("⚡ Start 1 Minute", callback_data="start:1M")],
        [InlineKeyboardButton("🎯 Select Channels", callback_data="targets")],
        [InlineKeyboardButton("🛑 Stop + Summary", callback_data="stop")],
    ]
    return InlineKeyboardMarkup(rows)

def kbd_targets() -> InlineKeyboardMarkup:
    rows = []
    for key in TARGETS.keys():
        enabled = "✅" if key in STATE.selected_targets else "⬜"
        rows.append([InlineKeyboardButton(f"{enabled} {key}", callback_data=f"toggle:{key}")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="back")])
    return InlineKeyboardMarkup(rows)

def fmt_signal(issue: str, pick: str, mode: str, step: int) -> str:
    emoji = "🟢" if pick == "BIG" else "🔴"
    return (
        f"<b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Mode:</b> {mode}\n"
        f"🎲 <b>Period:</b> <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔮 <b>PREDICTION:</b> {emoji} <b>{pick}</b> {emoji}\n"
        f"🧠 <b>Loss Step:</b> <b>{step}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"➕ <a href='{CHANNEL_LINK}'><b>JOIN CHANNEL</b></a>"
    )

def fmt_checking(issue: str) -> str:
    return (
        f"🔎 <b>Checking Result...</b>\n"
        f"🎲 Period: <code>{issue}</code>\n"
        f"⏳ Please wait..."
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
        f"🏆 Max Win Streak: <b>{s.max_streak_win}</b>\n"
        f"🎯 Accuracy: <b>{acc}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"🔗 <a href='{CHANNEL_LINK}'><b>REJOIN</b></a>"
    )

async def broadcast(context: ContextTypes.DEFAULT_TYPE, text: str, sticker: Optional[str]=None) -> None:
    for key in list(STATE.selected_targets):
        chat_id = TARGETS.get(key)
        if not chat_id:
            continue
        try:
            if sticker:
                await context.bot.send_sticker(chat_id, sticker)
            await context.bot.send_message(
                chat_id,
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logging.warning("Broadcast failed to %s: %s", key, e)

async def safe_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int, msg_id: int) -> None:
    try:
        await context.bot.delete_message(chat_id, msg_id)
    except Exception:
        pass

async def cleanup_checking_messages(context: ContextTypes.DEFAULT_TYPE) -> None:
    items = STATE.checking_msg_ids[:]
    STATE.checking_msg_ids.clear()
    for chat_id, msg_id in items:
        await safe_delete(context, chat_id, msg_id)

async def cleanup_loss_messages(context: ContextTypes.DEFAULT_TYPE) -> None:
    items = STATE.loss_msg_ids[:]
    STATE.loss_msg_ids.clear()
    for chat_id, msg_id in items:
        await safe_delete(context, chat_id, msg_id)

# =========================
# CORE LOOP (SAFE DEMO LOOP)
# =========================
async def engine_loop(context: ContextTypes.DEFAULT_TYPE, sid: int) -> None:
    """
    This loop demonstrates:
      - non-stop loop
      - graceful stop
      - checking message then delete
      - no extra signal after stop/summary
    It does NOT implement gambling prediction automation.
    """
    logging.info("Engine started sid=%s mode=%s", sid, STATE.mode)

    last_issue_seen = None

    while STATE.is_running and STATE.session_id == sid:
        data, status = await asyncio.to_thread(fetch_market_snapshot, STATE.mode)
        if not data:
            logging.warning("Market fetch failed: %s", status)
            await asyncio.sleep(1.5)
            continue

        issue = str(data.get("issueNumber", ""))
        number = str(data.get("number", ""))

        # prevent spam / duplicates
        if issue == last_issue_seen:
            await asyncio.sleep(0.8 if STATE.mode == "30S" else 1.5)
            continue
        last_issue_seen = issue

        # ✅ Placeholder pick (you replace with your own allowed logic)
        # Here we just map number >= 5 => BIG else SMALL
        pick = "BIG" if (number.isdigit() and int(number) >= 5) else "SMALL"

        # Send signal
        await broadcast(context, fmt_signal(issue, pick, STATE.mode, STATE.stats.streak_loss))

        # Send "checking..." then delete it later
        for key in list(STATE.selected_targets):
            chat_id = TARGETS.get(key)
            if not chat_id:
                continue
            try:
                msg = await context.bot.send_message(
                    chat_id,
                    fmt_checking(issue),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
                STATE.checking_msg_ids.append((chat_id, msg.message_id))
            except Exception:
                pass

        # Simulate result check (demo). Replace with your own allowed result reading.
        await asyncio.sleep(1.2 if STATE.mode == "30S" else 2.0)

        # Delete checking messages
        await cleanup_checking_messages(context)

        # Update stats (demo: random-ish)
        # You can replace this with real result comparison (if permitted).
        is_win = (int(time.time()) % 2 == 0)
        if is_win:
            STATE.stats.wins += 1
            STATE.stats.streak_win += 1
            STATE.stats.streak_loss = 0
            if STATE.stats.streak_win > STATE.stats.max_streak_win:
                STATE.stats.max_streak_win = STATE.stats.streak_win
        else:
            STATE.stats.losses += 1
            STATE.stats.streak_loss += 1
            STATE.stats.streak_win = 0

        await asyncio.sleep(0.8 if STATE.mode == "30S" else 1.5)

    logging.info("Engine exit sid=%s", sid)

# =========================
# HANDLERS
# =========================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in STATE.authorized:
        await update.message.reply_text(
            f"✅ <b>Unlocked</b>\n<b>{BRAND_NAME}</b>\nSelect option:",
            reply_markup=kbd_main(),
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            "🔒 <b>System Locked</b>\nSend password:",
            parse_mode=ParseMode.HTML,
        )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = (update.message.text or "").strip()

    if user_id not in STATE.authorized:
        if msg == BOT_PASSWORD and BOT_PASSWORD != "PASTE_PASSWORD_HERE":
            STATE.authorized.add(user_id)
            await update.message.reply_text(
                f"✅ <b>Access Granted</b>\nSelect option:",
                reply_markup=kbd_main(),
                parse_mode=ParseMode.HTML,
            )
        else:
            await update.message.reply_text("❌ Wrong password.", parse_mode=ParseMode.HTML)
        return

    await update.message.reply_text("Use the menu buttons 👇", reply_markup=kbd_main())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    user_id = query.from_user.id
    if user_id not in STATE.authorized:
        await query.edit_message_text("🔒 Locked. Send password in chat first.")
        return

    if data == "back":
        await query.edit_message_text("Select option:", reply_markup=kbd_main())
        return

    if data == "targets":
        await query.edit_message_text("🎯 Select target channels:", reply_markup=kbd_targets())
        return

    if data.startswith("toggle:"):
        key = data.split(":", 1)[1]
        if key in TARGETS:
            if key in STATE.selected_targets:
                STATE.selected_targets.remove(key)
            else:
                STATE.selected_targets.add(key)
        await query.edit_message_text("🎯 Select target channels:", reply_markup=kbd_targets())
        return

    if data.startswith("start:"):
        mode = data.split(":", 1)[1]
        if mode not in ("30S", "1M"):
            return

        # stop previous session safely
        STATE.session_id += 1
        STATE.is_running = False
        await asyncio.sleep(0.2)

        # start new session
        STATE.mode = mode
        STATE.is_running = True
        STATE.stats = SessionStats()
        sid = STATE.session_id

        await query.edit_message_text(
            f"✅ Started: <b>{mode}</b>\nTargets: <b>{', '.join(sorted(STATE.selected_targets))}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kbd_main(),
        )

        context.application.create_task(engine_loop(context, sid))
        return

    if data == "stop":
        # graceful stop: stop loop, cleanup, then summary, then ensure no extra signals
        STATE.session_id += 1
        STATE.is_running = False

        await cleanup_checking_messages(context)
        await cleanup_loss_messages(context)

        # broadcast summary
        await broadcast(context, fmt_summary())

        await query.edit_message_text("🛑 Stopped. Summary sent.", reply_markup=kbd_main())
        return

# =========================
# MAIN
# =========================
def main():
    logging.basicConfig(level=logging.INFO)

    if BOT_TOKEN == "PASTE_TOKEN_HERE" or not BOT_TOKEN or ":" not in BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing/invalid. Set BOT_TOKEN env var or paste it in code.")

    keep_alive()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Run forever
    application.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
