# ============================================
# PART 1 — BASE SETUP (NO ERROR)
# ============================================

import telebot
from telebot import types
import json, os, time, threading
from datetime import datetime

# ============================================
# BOT CONFIGURATION
# ============================================

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # <-- এখানে তোমার Bot Token দেবে
ADMIN_ID = 123456789                # <-- এখানে তোমার Telegram User ID দেবে

bot = telebot.TeleBot(BOT_TOKEN)

# ============================================
# DATA FOLDER & JSON FILES
# ============================================

DATA_DIR = "bot_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

FILES = {
    "settings": f"{DATA_DIR}/settings.json",
    "giveaway": f"{DATA_DIR}/giveaway.json",
    "participants": f"{DATA_DIR}/participants.json",
    "old_winners": f"{DATA_DIR}/old_winners.json"
}

# ============================================
# JSON LOADER & SAVER
# ============================================

def load(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ============================================
# DEFAULT FILES IF NOT EXISTS
# ============================================

if not os.path.exists(FILES["settings"]):
    save(FILES["settings"], {
        "verification_channels": [],
        "anti_duplicate": True,
        "old_winner_block": True,
        "auto_dm": True,
        "subscription_check": True,
        "username_required": True
    })

if not os.path.exists(FILES["participants"]):
    save(FILES["participants"], {"users": []})

if not os.path.exists(FILES["old_winners"]):
    save(FILES["old_winners"], {"user_ids": []})

# ============================================
# PART 2 — START COMMAND + ADMIN PANEL
# ============================================

# এগুলো পরে অন্য পার্টেও ব্যবহার করব (setup & winner state)
setup_state = {}
winner_state = {"winners": []}

# ---------------- /start --------------------
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    # যদি Admin হয়
    if msg.from_user.id == ADMIN_ID:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⚙️ Open Admin Panel", callback_data="open_panel"))

        bot.reply_to(
            msg,
            "┌⚡─────────────────────────────────────────────⚡┐\n"
            "🎉 WELCOME TO POWER POINT BREAK — GIVEAWAY BOT 🎉\n"
            "└⚡─────────────────────────────────────────────⚡┘\n\n"
            f"👑 Admin: @{msg.from_user.username}\n"
            "🛠️ Your Giveaway Control Panel Is Ready!\n\n"
            "📌 Tap below to open the panel.",
            reply_markup=kb
        )
    else:
        # Normal User View
        bot.reply_to(
            msg,
            "👋 Welcome to POWER POINT BREAK — GIVEAWAY BOT!\n\n"
            "🎁 All giveaways are posted in:\n"
            "📢 @PowerPointBreak\n\n"
            "Tap the JOIN button under giveaway posts to participate.\n"
            "Good luck 🍀"
        )

# ---------------- ADMIN PANEL (Common function) ----------------
def send_admin_panel(chat_id, message_id=None):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ Create New Giveaway", callback_data="new_giveaway"))
    kb.add(types.InlineKeyboardButton("👥 View Participants", callback_data="show_participants"))
    kb.add(types.InlineKeyboardButton("🏆 Select Winner", callback_data="manual_winner"))
    kb.add(types.InlineKeyboardButton("🛑 End Giveaway", callback_data="end_giveaway"))
    kb.add(types.InlineKeyboardButton("⚙️ Settings", callback_data="settings"))

    text = (
        "┌⚡──────────────────────────────────────────────⚡┐\n"
        "      🎛️ POWER POINT BREAK — ADMIN PANEL  \n"
        "└⚡──────────────────────────────────────────────⚡┘\n\n"
        "🛠️ Full Giveaway Control Loaded!"
    )

    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=kb)
    else:
        bot.send_message(chat_id, text, reply_markup=kb)

# --------------- /panel command -----------------
@bot.message_handler(commands=['panel'])
def cmd_panel(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    send_admin_panel(msg.chat.id)

# --------------- "⚙️ Open Admin Panel" button callback -----------
@bot.callback_query_handler(func=lambda c: c.data == "open_panel")
def cb_open_panel(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Only admin can open this panel.", show_alert=True)
        return
    send_admin_panel(call.message.chat.id, call.message.message_id)

# ============================================
# PART 3 — SETTINGS PANEL + TOGGLES
# ============================================

def on_off(value: bool) -> str:
    return "ON" if value else "OFF"

def send_settings_panel(chat_id, message_id=None):
    st = load(FILES["settings"])

    text = (
        "⚙️ SETTINGS PANEL\n\n"
        f"📢 Verification Channels: {len(st.get('verification_channels', []))}\n"
        f"🚫 Anti-Duplicate: {on_off(st.get('anti_duplicate', True))}\n"
        f"🔁 Old Winner Block: {on_off(st.get('old_winner_block', True))}\n"
        f"📨 Auto DM: {on_off(st.get('auto_dm', True))}\n"
        f"🔍 Subscription Check: {on_off(st.get('subscription_check', True))}\n"
        f"👤 Username Required: {on_off(st.get('username_required', True))}\n"
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📢 Add Channel", callback_data="add_channel"))
    kb.add(types.InlineKeyboardButton("🗑️ Remove Channel", callback_data="remove_channel"))
    kb.add(types.InlineKeyboardButton("🚫 Anti-Duplicate", callback_data="toggle_dup"))
    kb.add(types.InlineKeyboardButton("🔁 Old Winner Block", callback_data="toggle_old"))
    kb.add(types.InlineKeyboardButton("📨 Auto DM", callback_data="toggle_dm"))
    kb.add(types.InlineKeyboardButton("🔍 Subscription Check", callback_data="toggle_sub"))
    kb.add(types.InlineKeyboardButton("👤 Username Required", callback_data="toggle_usr"))

    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=kb)
    else:
        bot.send_message(chat_id, text, reply_markup=kb)

# ---- "⚙️ Settings" button থেকে Settings Panel খোলে ----
@bot.callback_query_handler(func=lambda c: c.data == "settings")
def cb_settings(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Only admin can open settings.", show_alert=True)
        return
    send_settings_panel(call.message.chat.id, call.message.message_id)

# ============================================
# TOGGLE BUTTONS
# ============================================

@bot.callback_query_handler(func=lambda c: c.data in ["toggle_dup", "toggle_old", "toggle_dm", "toggle_sub", "toggle_usr"])
def cb_toggles(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Only admin allowed.", show_alert=True)
        return

    st = load(FILES["settings"])

    if call.data == "toggle_dup":
        st["anti_duplicate"] = not st.get("anti_duplicate", True)
    elif call.data == "toggle_old":
        st["old_winner_block"] = not st.get("old_winner_block", True)
    elif call.data == "toggle_dm":
        st["auto_dm"] = not st.get("auto_dm", True)
    elif call.data == "toggle_sub":
        st["subscription_check"] = not st.get("subscription_check", True)
    elif call.data == "toggle_usr":
        st["username_required"] = not st.get("username_required", True)

    save(FILES["settings"], st)
    bot.answer_callback_query(call.id, "✅ Setting updated.", show_alert=False)
    send_settings_panel(call.message.chat.id, call.message.message_id)

# ============================================
# ADD / REMOVE CHANNELS
# ============================================

# Add Channel
@bot.callback_query_handler(func=lambda c: c.data == "add_channel")
def cb_add_channel(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Only admin allowed.", show_alert=True)
        return

    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "📢 Send channel usernames (one per line).\n\n"
        "Example:\n@PowerPointBreak\n@PPremiumHub\n@PPointWorld"
    )
    bot.register_next_step_handler(msg, process_add_channels)

def process_add_channels(message):
    if message.from_user.id != ADMIN_ID:
        return

    st = load(FILES["settings"])
    channels = st.get("verification_channels", [])

    lines = [l.strip() for l in message.text.splitlines() if l.strip()]
    for line in lines:
        if line.startswith("@") and line not in channels:
            channels.append(line)

    st["verification_channels"] = channels
    save(FILES["settings"], st)

    bot.reply_to(message, f"✅ Added {len(lines)} channel(s).\nTotal: {len(channels)}")
    send_settings_panel(message.chat.id)

# Remove Channel
@bot.callback_query_handler(func=lambda c: c.data == "remove_channel")
def cb_remove_channel(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Only admin allowed.", show_alert=True)
        return

    st = load(FILES["settings"])
    chs = st.get("verification_channels", [])
    if not chs:
        bot.answer_callback_query(call.id, "No channels to remove.", show_alert=True)
        return

    txt = "🗑️ Current Channels:\n\n"
    for idx, ch in enumerate(chs, start=1):
        txt += f"{idx}) {ch}\n"
    txt += "\nSend the number(s) you want to remove.\nExample: 1 or 1,3"

    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, txt)
    bot.register_next_step_handler(msg, process_remove_channels)

def process_remove_channels(message):
    if message.from_user.id != ADMIN_ID:
        return

    st = load(FILES["settings"])
    chs = st.get("verification_channels", [])

    raw = message.text.replace(" ", "")
    indexes = []
    for part in raw.split(","):
        if part.isdigit():
            idx = int(part)
            if 1 <= idx <= len(chs):
                indexes.append(idx-1)

    # বড় index আগে remove করলে সমস্যা হয় না
    indexes = sorted(set(indexes), reverse=True)
    removed = []
    for i in indexes:
        removed.append(chs[i])
        del chs[i]

    st["verification_channels"] = chs
    save(FILES["settings"], st)

    if removed:
        msg_txt = "✅ Removed:\n" + "\n".join(removed)
    else:
        msg_txt = "⚠️ No valid index found."

    bot.reply_to(message, msg_txt)
    send_settings_panel(message.chat.id)


# ============================================
# PART 4 — NEW GIVEAWAY SETUP (STEP 1–6)
# ============================================

# -------- Duration Text -> Seconds ----------
def parse_duration_to_seconds(text):
    """
    '30m' -> 1800
    '2h'  -> 7200
    '180' -> 10800 (ধরা হচ্ছে মিনিট)
    """
    t = text.strip().lower()
    try:
        if t.endswith("h"):
            n = int(t[:-1])
            return n * 60 * 60
        elif t.endswith("m"):
            n = int(t[:-1])
            return n * 60
        else:
            # শুধু সংখ্যা দিলে মিনিট ধরে নিলাম
            n = int(t)
            return n * 60
    except Exception:
        return None

# ---------- "➕ Create New Giveaway" button ----------
@bot.callback_query_handler(func=lambda c: c.data == "new_giveaway")
def cb_new_giveaway(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Only admin can create giveaway.", show_alert=True)
        return

    # নতুন setup শুরু করলাম
    setup_state["admin"] = {
        "step": 1,
        "title": None,
        "winner_count": None,
        "duration_seconds": None,
        "mode": None,
        "verification_channels": [],
        "old_winner_ids": [],
        "waiting_old_list": False
    }

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            "🎁 NEW GIVEAWAY SETUP STARTED\n\n"
            "Step 1️⃣: Send Giveaway Title\n\n"
            "Example:\n"
            "ChatGPT Plus — 1 Month\n"
            "YouTube Premium — 3 Months"
        )
    )

# ---------- ADMIN TEXT HANDLER (Steps 1–6) ----------
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def handle_admin_setup(m):
    # যদি setup চলছে না, তাহলে এই handler কিছু করবে না
    if "admin" not in setup_state:
        return

    state = setup_state["admin"]
    step = state.get("step", 0)

    # STEP 1 — TITLE
    if step == 1:
        title = m.text.strip()
        if len(title) < 3:
            bot.reply_to(m, "⚠️ Title খুব ছোট। আরেকটু Proper Title দিন।")
            return

        state["title"] = title
        state["step"] = 2

        bot.reply_to(
            m,
            "✅ Title Saved!\n\n"
            f"🎁 Giveaway: {title}\n\n"
            "Step 2️⃣: Winner কতজন হবে লিখুন (Number)\n"
            "Example: 1, 3, 10"
        )

    # STEP 2 — WINNER COUNT
    elif step == 2:
        try:
            count = int(m.text.strip())
            if count <= 0:
                raise ValueError
        except Exception:
            bot.reply_to(m, "⚠️ Valid সংখ্যা দিন (1, 3, 5...).")
            return

        state["winner_count"] = count
        state["step"] = 3

        bot.reply_to(
            m,
            "✅ Winner Count Saved!\n\n"
            f"🏆 Winners: {count}\n\n"
            "Step 3️⃣: Duration পাঠান.\n"
            "Example:\n"
            "30m  → 30 minutes\n"
            "1h   → 1 hour\n"
            "3h   → 3 hours"
        )

    # STEP 3 — DURATION
    elif step == 3:
        secs = parse_duration_to_seconds(m.text)
        if not secs or secs <= 0:
            bot.reply_to(m, "⚠️ Please send valid duration. Example: 30m, 1h, 3h")
            return

        state["duration_seconds"] = secs
        state["step"] = 4

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("🤖 Automatic Winner", callback_data="mode_auto"),
            types.InlineKeyboardButton("🧑‍⚖️ Manual Winner", callback_data="mode_manual")
        )

        bot.reply_to(
            m,
            "✅ Duration Saved!\n\n"
            f"⏳ Duration: {m.text.strip()}\n\n"
            "Step 4️⃣: Winner Mode Select করুন 🎯",
            reply_markup=kb
        )

    # STEP 5 — MULTI VERIFICATION CHANNELS
    elif step == 5:
        # এক বা একাধিক @channel প্রতি লাইনে
        lines = [line.strip() for line in m.text.splitlines() if line.strip()]
        channels = []
        for line in lines:
            if line.startswith("@") and line not in channels:
                channels.append(line)

        if not channels:
            bot.reply_to(
                m,
                "⚠️ অন্তত ১টা valid @channel দিন।\n"
                "Example:\n@PowerPointBreak\n@PPremiumHub"
            )
            return

        state["verification_channels"] = channels
        state["step"] = 6

        txt = "✅ Verification Channels Saved!\n\nChannels:\n"
        for ch in channels:
            txt += f"• {ch}\n"

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("🚫 Block Old Winners", callback_data="old_block_yes"),
            types.InlineKeyboardButton("⏭️ Skip", callback_data="old_block_skip")
        )

        bot.reply_to(
            m,
            txt + "\nStep 6️⃣: Old Winners Filter\n\n"
            "আগের Winners দের block করতে চান?",
            reply_markup=kb
        )

    # STEP 6 — OLD WINNER LIST INPUT (যদি YES চাপা থাকে)
    elif step == 6 and state.get("waiting_old_list", False):
        lines = [line.strip() for line in m.text.splitlines() if line.strip()]
        old_ids = []

        for line in lines:
            if "|" in line:
                parts = line.split("|", 1)
                userid_str = parts[1].strip()
                # শুধু Digit রেখে ID ধরব
                userid_str = "".join(ch for ch in userid_str if ch.isdigit())
                if userid_str:
                    try:
                        old_ids.append(int(userid_str))
                    except Exception:
                        pass

        state["old_winner_ids"] = old_ids
        state["waiting_old_list"] = False

        # সব ডাটা giveaway.json এ সেভ
        giveaway_data = {
            "active": False,
            "title": state["title"],
            "winner_count": state["winner_count"],
            "duration_seconds": state["duration_seconds"],
            "mode": state["mode"],  # "AUTO" বা "MANUAL"
            "verification_channels": state["verification_channels"],
            "old_winner_ids": state["old_winner_ids"],
            "message_chat_id": None,
            "message_id": None,
            "start_time": None,
            "end_time": None
        }
        save(FILES["giveaway"], giveaway_data)

        txt = (
            "✅ Old Winner IDs Saved!\n"
            f"Total Old Winners Blocked: {len(old_ids)}\n\n"
            "✅ Giveaway Setup Completed (DATA SAVED).\n"
            "এখন /startgiveaway দিয়ে Giveaway শুরু করতে পারবেন।"
        )
        bot.reply_to(m, txt)

        # setup শেষ, state clear
        setup_state.pop("admin", None)


# ============================================
# PART 5 — START GIVEAWAY + TIMER + JOIN SYSTEM
# ============================================

def format_time_left(seconds_left: int) -> str:
    """Seconds থেকে HH:MM:SS বানায়"""
    if seconds_left < 0:
        seconds_left = 0
    h = seconds_left // 3600
    m = (seconds_left % 3600) // 60
    s = seconds_left % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def make_progress_bar(pct: float) -> str:
    """0–100% থেকে 10 টা ব্লকে Progress Bar বানায়"""
    if pct < 0:
        pct = 0
    if pct > 100:
        pct = 100
    total_blocks = 10
    filled = int(round((pct / 100) * total_blocks))
    if filled > total_blocks:
        filled = total_blocks
    bar = "▰" * filled + "▱" * (total_blocks - filled)
    return bar

def build_giveaway_text(giveaway: dict, participants_count: int, time_left_sec: int, progress_pct: float) -> str:
    """Main Giveaway Post এর Text বানায় (RGB Mode)"""
    title = giveaway.get("title", "Unknown")
    winner_count = giveaway.get("winner_count", 1)
    mode = giveaway.get("mode", "AUTO")
    old_block = len(giveaway.get("old_winner_ids", [])) > 0

    time_str = format_time_left(time_left_sec)
    bar = make_progress_bar(progress_pct)

    txt = (
        "┌⚡────────────────────────────────────────────────⚡┐\n"
        "🌈 POWER POINT BREAK — GIVEAWAY STARTED (RGB MODE)\n"
        "└⚡────────────────────────────────────────────────⚡┘\n\n"
        f"🎁 Giveaway: {title}\n\n"
        f"🏆 Winners: {winner_count}\n"
        f"🎯 Mode: {mode}\n\n"
        "⚠️ Must Join All Verification Channels\n"
    )

    if old_block:
        txt += "❌ OLD WINNERS ARE BANNED ❌\n\n"
    else:
        txt += "\n"

    txt += (
        f"⏳ Time Left: {time_str}\n"
        f"⌛ Progress: {int(round(progress_pct))}%\n\n"
        f"{bar}\n\n"
        f"👥 Participants: {participants_count}\n\n"
        "👇 Tap to Join"
    )
    return txt

def start_timer_thread():
    """Background Timer Thread Start করে"""
    t = threading.Thread(target=timer_loop, daemon=True)
    t.start()

def timer_loop():
    """প্রতি কয়েক সেকেন্ড পরপর Giveaway Post update করে (Time + Progress + Count)"""
    while True:
        g = load(FILES["giveaway"])
        if not g or not g.get("active"):
            break

        start_time = g.get("start_time")
        end_time = g.get("end_time")
        duration = g.get("duration_seconds", 0)

        if not start_time or not end_time or duration <= 0:
            break

        now = int(time.time())
        time_left = end_time - now
        elapsed = now - start_time

        if time_left <= 0:
            # Time over
            g["active"] = False
            save(FILES["giveaway"], g)

            try:
                participants_data = load(FILES["participants"])
                participants_count = len(participants_data.get("users", []))
                text = build_giveaway_text(g, participants_count, 0, 100)

                join_kb = types.InlineKeyboardMarkup()
                join_kb.add(types.InlineKeyboardButton("❤️ JOIN GIVEAWAY NOW 🌹", callback_data="join_giveaway"))

                bot.edit_message_text(
                    chat_id=g["message_chat_id"],
                    message_id=g["message_id"],
                    text=text,
                    reply_markup=join_kb
                )
            except Exception:
                pass
            break

        progress_pct = (elapsed / duration) * 100 if duration > 0 else 0

        try:
            participants_data = load(FILES["participants"])
            participants_count = len(participants_data.get("users", []))
            text = build_giveaway_text(g, participants_count, time_left, progress_pct)

            join_kb = types.InlineKeyboardMarkup()
            join_kb.add(types.InlineKeyboardButton("❤️ JOIN GIVEAWAY NOW 🌹", callback_data="join_giveaway"))

            bot.edit_message_text(
                chat_id=g["message_chat_id"],
                message_id=g["message_id"],
                text=text,
                reply_markup=join_kb
            )
        except Exception:
            # Message edit error হলে ignore করব
            pass

        time.sleep(10)  # প্রতি 10 সেকেন্ডে Update (ইচ্ছা হলে 5 করতেও পারো)

# ============================================
# /startgiveaway — ADMIN GIVEAWAY START
# ============================================

@bot.message_handler(commands=['startgiveaway'])
def cmd_start_giveaway(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.reply_to(msg, "Only admin can start the giveaway.")
        return

    g = load(FILES["giveaway"])
    if not g or not g.get("title"):
        bot.reply_to(msg, "⚠️ No giveaway setup found.\n\n/panel → ➕ Create New Giveaway দিয়ে আগে setup করুন।")
        return

    if g.get("active"):
        bot.reply_to(msg, "⚠️ A giveaway is already active.")
        return

    # পুরোনো participants reset
    save(FILES["participants"], {"users": []})

    # Main Post কোন Channel এ যাবে → Verification Channels এর প্রথমটা, নাহলে current chat
    channels = g.get("verification_channels", [])
    if channels:
        main_chat_id = channels[0]   # Bot must be admin in this channel
    else:
        main_chat_id = msg.chat.id   # Fallback: current chat

    duration = g.get("duration_seconds", 0)
    now_ts = int(time.time())
    g["start_time"] = now_ts
    g["end_time"] = now_ts + duration
    g["active"] = True

    participants_count = 0
    time_left = duration
    progress_pct = 0

    join_kb = types.InlineKeyboardMarkup()
    join_btn = types.InlineKeyboardButton("❤️ JOIN GIVEAWAY NOW 🌹", callback_data="join_giveaway")
    join_kb.add(join_btn)

    text = build_giveaway_text(g, participants_count, time_left, progress_pct)

    # Channel এ প্রথম Giveaway Post
    sent = bot.send_message(main_chat_id, text, reply_markup=join_kb)

    g["message_chat_id"] = sent.chat.id
    g["message_id"] = sent.message_id
    save(FILES["giveaway"], g)

    bot.reply_to(msg, "✅ Giveaway started successfully!")
    start_timer_thread()

# ============================================
# JOIN BUTTON → ALL CHECKS + POPUP
# ============================================

@bot.callback_query_handler(func=lambda c: c.data == "join_giveaway")
def cb_join_giveaway(call):
    user = call.from_user
    user_id = user.id
    username = user.username

    g = load(FILES["giveaway"])
    if not g or not g.get("active"):
        bot.answer_callback_query(call.id, "⏳ This giveaway has already ended!", show_alert=True)
        return

    settings = load(FILES["settings"])
    participants_data = load(FILES["participants"])
    users = participants_data.get("users", [])

    # Username Required
    if settings.get("username_required", True) and not username:
        bot.answer_callback_query(
            call.id,
            "❌ You must set a Telegram username to join this giveaway.",
            show_alert=True
        )
        return

    # Anti-Duplicate (একজন একবার join)
    if settings.get("anti_duplicate", True):
        for u in users:
            if u.get("id") == user_id:
                bot.answer_callback_query(
                    call.id,
                    "⚠️ You already joined this giveaway!",
                    show_alert=True
                )
                return

    # Old Winner Block (UserID দিয়ে চেক)
    if settings.get("old_winner_block", True):
        old_ids = g.get("old_winner_ids", [])
        if user_id in old_ids:
            bot.answer_callback_query(
                call.id,
                "❌ You are already a previous winner.\nThis giveaway is for new participants only.",
                show_alert=True
            )
            return

    # Subscription Check — সব Verification Channels join করেছে কিনা
    if settings.get("subscription_check", True):
        channels = g.get("verification_channels", [])
        for ch in channels:
            try:
                member = bot.get_chat_member(ch, user_id)
                if member.status not in ["member", "administrator", "creator"]:
                    raise Exception("Not joined")
            except Exception:
                bot.answer_callback_query(
                    call.id,
                    "📢 Please join all required channels to enter the giveaway!",
                    show_alert=True
                )
                return

    # সব ঠিক থাকলে → Participant Add
    users.append({
        "id": user_id,
        "username": username,
        "joined_at": datetime.utcnow().isoformat()
    })
    participants_data["users"] = users
    save(FILES["participants"], participants_data)

    bot.answer_callback_query(
        call.id,
        "🎉 You successfully joined the giveaway!\nGood luck 🍀",
        show_alert=True
    )


# ============================================
# PART 6 — PARTICIPANTS + WINNERS + RESULT + END
# ============================================

import random  # random winner select করার জন্য

def pick_random_winners(giveaway, participants_data):
    """Old winner UserID বাদ দিয়ে random winners select করে।"""
    users = participants_data.get("users", [])
    if not users:
        return []

    winner_count = giveaway.get("winner_count", 1)
    old_ids = set(giveaway.get("old_winner_ids", []))

    # Old winner বাদ দিয়ে eligible list বানালাম
    eligible = [u for u in users if u.get("id") not in old_ids]

    # যদি কেউ eligible না থাকে → সব user থেকেই select করব
    if not eligible:
        eligible = users

    k = min(winner_count, len(eligible))
    if k <= 0:
        return []

    return random.sample(eligible, k)

def build_result_text(giveaway, winners_list):
    """Final RESULT পোস্টের টেক্সট বানায়।"""
    title = giveaway.get("title", "Unknown Giveaway")
    winner_count = len(winners_list)

    txt = (
        "┌⚡────────────────────────────────────────────────⚡┐\n"
        "🎉 POWER POINT BREAK — GIVEAWAY RESULT 🎉\n"
        "└⚡────────────────────────────────────────────────⚡┘\n\n"
        f"🏆 Winners ({winner_count}):\n\n"
    )

    if winner_count == 0:
        txt += "⚠️ No winners could be selected.\n\n"
    else:
        idx = 1
        for w in winners_list:
            uname = w.get("username")
            uid = w.get("id")
            if uname:
                txt += f"{idx}) @{uname}  |  {uid}\n"
            else:
                txt += f"{idx}) (no_username)  |  {uid}\n"
            idx += 1
        txt += "\n"

    txt += (
        f"🎁 Reward: {title}\n\n"
        "Hosted By: POWER POINT BREAK\n"
        "Admin: @MinexxProo"
    )
    return txt

# ============================================
# /participants — সব Join করা ইউজারের লিস্ট
# ============================================

@bot.message_handler(commands=['participants'])
def cmd_participants(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    pdata = load(FILES["participants"])
    users = pdata.get("users", [])

    if not users:
        bot.reply_to(msg, "👥 No participants yet.")
        return

    lines = ["👥 PARTICIPANTS LIST:\n"]
    idx = 1
    for u in users:
        uname = u.get("username")
        uid = u.get("id")
        if uname:
            lines.append(f"{idx}) @{uname}  |  {uid}")
        else:
            lines.append(f"{idx}) (no_username)  |  {uid}")
        idx += 1

    text = "\n".join(lines)
    bot.reply_to(msg, text)

# ============================================
# /winner — AUTO WINNER PICK + ADMIN APPROVAL
# ============================================

@bot.message_handler(commands=['winner'])
def cmd_winner(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    g = load(FILES["giveaway"])
    if not g or not g.get("title"):
        bot.reply_to(msg, "⚠️ No giveaway data found.")
        return

    pdata = load(FILES["participants"])
    users = pdata.get("users", [])
    if not users:
        bot.reply_to(msg, "⚠️ No participants to pick winners from.")
        return

    winners = pick_random_winners(g, pdata)
    if not winners:
        bot.reply_to(msg, "⚠️ Could not select any winners.")
        return

    # global winner_state (Part 2 তে ডিফাইন ছিল)
    winner_state["winners"] = winners

    prev = "🤖 AUTO WINNERS (Preview):\n\n"
    idx = 1
    for w in winners:
        uname = w.get("username")
        uid = w.get("id")
        if uname:
            prev += f"{idx}) @{uname}  |  {uid}\n"
        else:
            prev += f"{idx}) (no_username)  |  {uid}\n"
        idx += 1

    prev += "\nDo you want to post this result in the giveaway channel?"

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ APPROVE & POST", callback_data="approve_winners"),
        types.InlineKeyboardButton("❌ CANCEL", callback_data="cancel_winners")
    )

    bot.reply_to(msg, prev, reply_markup=kb)

# ============================================
# WINNER APPROVAL CALLBACK
# ============================================

@bot.callback_query_handler(func=lambda c: c.data in ["approve_winners", "cancel_winners"])
def cb_winner_approval(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Only admin can approve.", show_alert=True)
        return

    g = load(FILES["giveaway"])

    if call.data == "cancel_winners":
        winner_state["winners"] = []
        bot.answer_callback_query(call.id, "❌ Winner announcement cancelled.", show_alert=True)
        bot.send_message(call.message.chat.id, "❌ Winner announcement cancelled.")
        return

    winners = winner_state.get("winners", [])
    if not winners:
        bot.answer_callback_query(call.id, "⚠️ No winner data found.", show_alert=True)
        return

    # RESULT TEXT বানালাম
    result_text = build_result_text(g, winners)

    # Main channel = যেখানে Giveaway পোস্ট হয়েছিল
    main_chat_id = g.get("message_chat_id") or call.message.chat.id

    try:
        bot.send_message(main_chat_id, result_text)
    except Exception:
        bot.send_message(call.message.chat.id, result_text)

    bot.answer_callback_query(call.id, "✅ Winners posted!", show_alert=True)
    bot.send_message(call.message.chat.id, "✅ Winners have been posted in the channel.")

    # Auto DM থাকলে Winner দের DM পাঠাবো
    settings = load(FILES["settings"])
    if settings.get("auto_dm", True):
        for w in winners:
            uid = w.get("id")
            try:
                bot.send_message(
                    uid,
                    "🎉 Congratulations!\n"
                    "You won the giveaway from POWER POINT BREAK!\n\n"
                    "Please contact: @MinexxProo"
                )
            except Exception:
                # user DM বন্ধ করলে error ignore
                pass

    # Old Winners list update (UserID ভিত্তিক)
    g_old_ids = set(g.get("old_winner_ids", []))
    for w in winners:
        g_old_ids.add(w.get("id"))
    g["old_winner_ids"] = list(g_old_ids)
    g["active"] = False
    save(FILES["giveaway"], g)

    # Global winner_state clear
    winner_state["winners"] = []

# ============================================
# /end — ADMIN FORCEFULLY END GIVEAWAY
# ============================================

@bot.message_handler(commands=['end'])
def cmd_end(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    g = load(FILES["giveaway"])
    if not g or not g.get("active"):
        bot.reply_to(msg, "⚠️ No active giveaway to end.")
        return

    g["active"] = False
    save(FILES["giveaway"], g)

    bot.reply_to(msg, "🛑 Giveaway has been ended by admin.\nNow use /winner to pick winners.")

# ============================================
# BOT RUN
# ============================================

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
