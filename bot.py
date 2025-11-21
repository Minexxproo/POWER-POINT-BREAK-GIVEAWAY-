# ====================================================
# POWER POINT BREAK — GIVEAWAY BOT (FINAL FULL VERSION)
# ====================================================

import telebot
from telebot import types
import json, os, time, threading, random
from datetime import datetime

# ==========================
# BOT CONFIG
# ==========================

BOT_TOKEN = "8448847868:AAExU9oq6UTMbqvWm0Ja7u0cHjP5PX-otjI"    # <-- তোমার Bot Token
ADMIN_ID = 5692210187                 # <-- তোমার Telegram Numeric ID

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================
# DATA FOLDERS
# ==========================

DATA_DIR = "bot_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

FILES = {
    "settings": f"{DATA_DIR}/settings.json",
    "giveaway": f"{DATA_DIR}/giveaway.json",
    "participants": f"{DATA_DIR}/participants.json",
    "old_winners": f"{DATA_DIR}/old_winners.json"
}

# ==========================
# JSON FUNCTIONS
# ==========================

def load(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ==========================
# DEFAULT FILES
# ==========================

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

# ==========================
# SESSION STORAGE
# ==========================

setup_state = {}
winner_state = {"winners": []}

# =====================================================
# PART 1 — START & PANEL
# =====================================================

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    if msg.from_user.id == ADMIN_ID:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⚙️ Open Admin Panel", callback_data="open_panel"))

        bot.reply_to(
            msg,
            "┌⚡─────────────────────────────────────────────⚡┐\n"
            "🎉 WELCOME TO POWER POINT BREAK — GIVEAWAY BOT 🎉\n"
            "└⚡─────────────────────────────────────────────⚡┘\n\n"
            "👑 Admin Panel Ready!\n\n"
            "📌 Tap below to continue 👇",
            reply_markup=kb
        )
    else:
        bot.reply_to(
            msg,
            "👋 Welcome!\n"
            "All giveaways are posted in: @PowerPointBreak\n"
            "Tap ‘JOIN’ under the giveaway post to participate!"
        )

# PANEL BUTTON
def send_admin_panel(chat_id, msg_id=None):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ Create New Giveaway", callback_data="new_giveaway"))
    kb.add(types.InlineKeyboardButton("👥 View Participants", callback_data="show_participants"))
    kb.add(types.InlineKeyboardButton("🏆 Select Winner", callback_data="manual_winner"))
    kb.add(types.InlineKeyboardButton("🛑 End Giveaway", callback_data="end_giveaway"))
    kb.add(types.InlineKeyboardButton("⚙️ Settings", callback_data="settings"))

    text = (
        "┌⚡──────────────────────────────────────────────⚡┐\n"
        "      🎛️ POWER POINT BREAK — ADMIN PANEL  \n"
        "└⚡──────────────────────────────────────────────⚡┘"
    )

    if msg_id:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text, reply_markup=kb)
    else:
        bot.send_message(chat_id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "open_panel")
def cb_open_panel(call):
    if call.from_user.id != ADMIN_ID:
        return
    send_admin_panel(call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['panel'])
def cmd_panel(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    send_admin_panel(msg.chat.id)

# =====================================================
# PART 2 — SETTINGS PANEL
# =====================================================

def on_off(v):
    return "ON" if v else "OFF"

def send_settings_panel(chat_id, msg_id=None):
    st = load(FILES["settings"])

    text = (
        "⚙️ SETTINGS PANEL\n\n"
        f"📢 Channels: {len(st['verification_channels'])}\n"
        f"🚫 Anti-Duplicate: {on_off(st['anti_duplicate'])}\n"
        f"🔁 Old Winner Block: {on_off(st['old_winner_block'])}\n"
        f"📨 Auto DM: {on_off(st['auto_dm'])}\n"
        f"🔍 Subscription Check: {on_off(st['subscription_check'])}\n"
        f"👤 Username Required: {on_off(st['username_required'])}\n"
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📢 Add Channel", callback_data="add_channel"))
    kb.add(types.InlineKeyboardButton("🗑 Remove Channel", callback_data="remove_channel"))
    kb.add(types.InlineKeyboardButton("🚫 Anti-Duplicate", callback_data="toggle_dup"))
    kb.add(types.InlineKeyboardButton("🔁 Old Winner Block", callback_data="toggle_old"))
    kb.add(types.InlineKeyboardButton("📨 Auto DM", callback_data="toggle_dm"))
    kb.add(types.InlineKeyboardButton("🔍 Subscription Check", callback_data="toggle_sub"))
    kb.add(types.InlineKeyboardButton("👤 Username Required", callback_data="toggle_usr"))

    if msg_id:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text, reply_markup=kb)
    else:
        bot.send_message(chat_id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "settings")
def cb_settings(call):
    if call.from_user.id != ADMIN_ID:
        return
    send_settings_panel(call.message.chat.id, call.message.message_id)

# TOGGLE HANDLER
@bot.callback_query_handler(func=lambda c: c.data in ["toggle_dup","toggle_old","toggle_dm","toggle_sub","toggle_usr"])
def cb_toggle(call):
    if call.from_user.id != ADMIN_ID:
        return

    st = load(FILES["settings"])

    mapping = {
        "toggle_dup": "anti_duplicate",
        "toggle_old": "old_winner_block",
        "toggle_dm": "auto_dm",
        "toggle_sub": "subscription_check",
        "toggle_usr": "username_required"
    }

    key = mapping[call.data]
    st[key] = not st[key]
    save(FILES["settings"], st)

    send_settings_panel(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Updated", show_alert=False)

# ADD CHANNEL
@bot.callback_query_handler(func=lambda c: c.data == "add_channel")
def cb_add_ch(call):
    if call.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(call.message.chat.id,"📢 Send channels (one per line):")
    bot.register_next_step_handler(msg, add_ch_step)

def add_ch_step(m):
    st = load(FILES["settings"])
    ch = st["verification_channels"]

    for line in m.text.splitlines():
        if line.startswith("@") and line not in ch:
            ch.append(line.strip())

    save(FILES["settings"], st)
    send_settings_panel(m.chat.id)
    bot.reply_to(m, "✅ Channels Added!")

# REMOVE CHANNEL
@bot.callback_query_handler(func=lambda c: c.data == "remove_channel")
def cb_rem_ch(call):
    st = load(FILES["settings"])
    ch = st["verification_channels"]

    if not ch:
        bot.answer_callback_query(call.id, "No channels", show_alert=True)
        return

    txt = "🗑 Channels:\n"
    for i, c in enumerate(ch,1):
        txt += f"{i}) {c}\n"
    txt += "\nSend numbers (1 or 1,2)"

    msg = bot.send_message(call.message.chat.id,txt)
    bot.register_next_step_handler(msg, rem_ch_step)

def rem_ch_step(m):
    st = load(FILES["settings"])
    ch = st["verification_channels"]
    nums = m.text.replace(" ","").split(",")

    idxs=[]
    for n in nums:
        if n.isdigit():
            x=int(n)
            if 1<=x<=len(ch): idxs.append(x-1)

    idxs=sorted(set(idxs),reverse=True)
    for i in idxs: ch.pop(i)

    save(FILES["settings"],st)
    bot.reply_to(m,"Removed!")
    send_settings_panel(m.chat.id)

# =====================================================
# PART 3 — NEW GIVEAWAY SETUP
# =====================================================

def parse_duration(s):
    s=s.lower().strip()
    if s.endswith("h"):
        return int(s[:-1])*3600
    if s.endswith("m"):
        return int(s[:-1])*60
    if s.isdigit():
        return int(s)*60
    return None

@bot.callback_query_handler(func=lambda c: c.data=="new_giveaway")
def cb_new(call):
    setup_state["admin"]={
        "step":1,
        "title":None,
        "winner":None,
        "duration":None,
        "mode":None,
        "channels":[],
        "old_ids":[],
        "waiting_old":False
    }
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🎁 Step 1️⃣ Send Giveaway Title"
    )

@bot.message_handler(func=lambda m: m.from_user.id==ADMIN_ID)
def setup_handler(m):
    if "admin" not in setup_state:
        return

    st=setup_state["admin"]
    step=st["step"]

    # STEP 1 → TITLE
    if step==1:
        st["title"]=m.text
        st["step"]=2
        bot.reply_to(m,"Step 2️⃣ Send Winner Count (1,2,3...)")
        return

    # STEP 2 → WINNER COUNT
    if step==2:
        if not m.text.isdigit():
            bot.reply_to(m,"Send number only.")
            return
        st["winner"]=int(m.text)
        st["step"]=3
        bot.reply_to(m,"Step 3️⃣ Send Duration (30m,1h...)")
        return

    # STEP 3 → DURATION
    if step==3:
        sec=parse_duration(m.text)
        if not sec:
            bot.reply_to(m,"Invalid Duration.")
            return
        st["duration"]=sec
        st["step"]=4

        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🤖 Automatic Winner",callback_data="mode_auto"))
        kb.add(types.InlineKeyboardButton("🧑‍⚖️ Manual Winner",callback_data="mode_manual"))

        bot.reply_to(
            m,
            "Step 4️⃣ Select Winner Mode",
            reply_markup=kb
        )
        return

    # STEP 5 → CHANNEL LIST
    if step==5:
        ch=[]
        for line in m.text.splitlines():
            if line.startswith("@"):
                ch.append(line.strip())

        if not ch:
            bot.reply_to(m,"Send @channels properly.")
            return

        st["channels"]=ch
        st["step"]=6

        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🚫 Block Old Winner",callback_data="old_yes"))
        kb.add(types.InlineKeyboardButton("⏭ Skip",callback_data="old_no"))

        bot.reply_to(
            m,
            "Step 6️⃣ Old Winner Block?",
            reply_markup=kb
        )
        return

    # STEP 6 → OLD WINNER LIST
    if step==6 and st["waiting_old"]:
        ids=[]
        for line in m.text.splitlines():
            if "|" in line:
                uid="".join(ch for ch in line.split("|")[1] if ch.isdigit())
                if uid:
                    ids.append(int(uid))

        st["old_ids"]=ids
        st["waiting_old"]=False

        finish_giveaway_setup(m, st)
        return

# WINNER MODE CALLBACK
@bot.callback_query_handler(func=lambda c: c.data in ["mode_auto","mode_manual"])
def cb_mode(call):
    if call.from_user.id!=ADMIN_ID:
        return

    st=setup_state["admin"]

    if call.data=="mode_auto":
        st["mode"]="AUTO"
    else:
        st["mode"]="MANUAL"

    st["step"]=5

    bot.answer_callback_query(call.id,"Mode Saved!",show_alert=True)
    bot.send_message(call.message.chat.id,"Send Verification Channels (@abc per line)")

def finish_giveaway_setup(m, st):
    giveaway={
        "active":False,
        "title":st["title"],
        "winner_count":st["winner"],
        "duration_seconds":st["duration"],
        "mode":st["mode"],
        "verification_channels":st["channels"],
        "old_winner_ids":st["old_ids"],
        "message_chat_id":None,
        "message_id":None,
        "start_time":None,
        "end_time":None
    }

    save(FILES["giveaway"],giveaway)
    bot.reply_to(m,"✅ Giveaway Setup Completed!\nUse /startgiveaway to start.")
    setup_state.pop("admin",None)

@bot.callback_query_handler(func=lambda c: c.data in ["old_yes","old_no"])
def cb_old(call):
    st=setup_state["admin"]

    if call.data=="old_no":
        st["old_ids"]=[]
        finish_giveaway_setup(call.message, st)
        bot.answer_callback_query(call.id,"Skipped!",show_alert=False)
        return

    st["waiting_old"]=True
    bot.answer_callback_query(call.id,"Send old winners list",show_alert=False)
    bot.send_message(call.message.chat.id,"Send like:\n@name | 12345678")

# =====================================================
# PART 4 — START GIVEAWAY + TIMER
# =====================================================

def format_time(s):
    h=s//3600
    m=(s%3600)//60
    sec=s%60
    return f"{h:02d}:{m:02d}:{sec:02d}"

def bar(p):
    filled=int(p/10)
    return "▰"*filled+"▱"*(10-filled)

def build_text(g, count, left, pct):
    title=g["title"]
    mode=g["mode"]
    wc=g["winner_count"]

    txt = (
        "┌⚡────────────────────────────────────────────────⚡┐\n"
        "🌈 POWER POINT BREAK — GIVEAWAY STARTED (RGB MODE)\n"
        "└⚡────────────────────────────────────────────────⚡┘\n\n"
        f"🎁 Giveaway: {title}\n\n"
        f"🏆 Winners: {wc}\n"
        f"🎯 Mode: {mode}\n\n"
        "⚠️ Must Join All Verification Channels\n"
    )

    if g["old_winner_ids"]:
        txt+="❌ OLD WINNERS ARE BANNED ❌\n\n"

    txt+=(
        f"⏳ Time Left: {format_time(left)}\n"
        f"⌛ Progress: {int(pct)}%\n\n"
        f"{bar(pct)}\n\n"
        f"👥 Participants: {count}\n\n"
        "👇 Tap to Join"
    )
    return txt

@bot.message_handler(commands=['startgiveaway'])
def start_g(msg):
    if msg.from_user.id!=ADMIN_ID:
        return

    g=load(FILES["giveaway"])
    if not g.get("title"):
        bot.reply_to(msg,"No giveaway setup!")
        return

    save(FILES["participants"],{"users":[]})

    channels=g["verification_channels"]
    if channels:
        chat_id=channels[0]
    else:
        chat_id=msg.chat.id

    now=int(time.time())
    g["start_time"]=now
    g["end_time"]=now+g["duration_seconds"]
    g["active"]=True

    text=build_text(g,0,g["duration_seconds"],0)

    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❤️ JOIN GIVEAWAY NOW 🌹",callback_data="join_g"))

    sent=bot.send_message(chat_id,text,reply_markup=kb)

    g["message_chat_id"]=sent.chat.id
    g["message_id"]=sent.message_id
    save(FILES["giveaway"],g)

    bot.reply_to(msg,"Giveaway Started!")
    start_timer()

def start_timer():
    t=threading.Thread(target=timer,daemon=True)
    t.start()

def timer():
    while True:
        g=load(FILES["giveaway"])
        if not g.get("active"):
            break

        now=int(time.time())
        start=g["start_time"]
        end=g["end_time"]
        dur=g["duration_seconds"]
        left=end-now
        if left<=0:
            left=0

        elapsed=now-start
        pct=(elapsed/dur)*100 if dur>0 else 100

        pdata=load(FILES["participants"])
        count=len(pdata["users"])

        text=build_text(g,count,left,pct)

        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("❤️ JOIN GIVEAWAY NOW 🌹",callback_data="join_g"))

        try:
            bot.edit_message_text(
                chat_id=g["message_chat_id"],
                message_id=g["message_id"],
                text=text,
                reply_markup=kb
            )
        except:
            pass

        if left<=0:
            g["active"]=False
            save(FILES["giveaway"],g)
            break

        time.sleep(5)

# =====================================================
# JOIN SYSTEM
# =====================================================

@bot.callback_query_handler(func=lambda c: c.data=="join_g")
def join(call):
    user=call.from_user
    uid=user.id
    uname=user.username

    g=load(FILES["giveaway"])
    if not g.get("active"):
        bot.answer_callback_query(call.id,"Ended!",show_alert=True)
        return

    st=load(FILES["settings"])
    pdata=load(FILES["participants"])
    users=pdata["users"]

    # Username required
    if st["username_required"] and not uname:
        bot.answer_callback_query(call.id,"Set a Username!",show_alert=True)
        return

    # Duplicate prevent
    if st["anti_duplicate"]:
        for u in users:
            if u["id"]==uid:
                bot.answer_callback_query(call.id,"You already joined!",show_alert=True)
                return

    # Old winner block
    if st["old_winner_block"] and uid in g["old_winner_ids"]:
        bot.answer_callback_query(call.id,"Old winners can't join!",show_alert=True)
        return

    # Subscription check
    if st["subscription_check"]:
        for ch in g["verification_channels"]:
            try:
                status=bot.get_chat_member(ch,uid).status
                if status not in ["member","administrator","creator"]:
                    raise Exception
            except:
                bot.answer_callback_query(call.id,"Join all channels first!",show_alert=True)
                return

    users.append({"id":uid,"username":uname})
    pdata["users"]=users
    save(FILES["participants"],pdata)

    bot.answer_callback_query(call.id,"🎉 You Joined!\nGood Luck 🍀",show_alert=True)

# =====================================================
# WINNER PICK
# =====================================================

@bot.message_handler(commands=['winner'])
def winner_cmd(msg):
    if msg.from_user.id!=ADMIN_ID:
        return

    g=load(FILES["giveaway"])
    pdata=load(FILES["participants"])
    users=pdata["users"]

    if not users:
        bot.reply_to(msg,"No participants.")
        return

    # Remove old winners
    eligible=[u for u in users if u["id"] not in g["old_winner_ids"]]
    if not eligible:
        eligible=users

    count=g["winner_count"]
    w=random.sample(eligible,min(count,len(eligible)))

    winner_state["winners"]=w

    txt="🤖 WINNER PREVIEW:\n\n"
    for i,u in enumerate(w,1):
        txt += f"{i}) @{u['username']} | {u['id']}\n"

    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ APPROVE",callback_data="approve"))
    kb.add(types.InlineKeyboardButton("❌ CANCEL",callback_data="cancel"))

    bot.reply_to(msg,txt,reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data in ["approve","cancel"])
def win_approve(call):
    if call.from_user.id!=ADMIN_ID:
        return

    if call.data=="cancel":
        winner_state["winners"]=[]
        bot.answer_callback_query(call.id,"Cancelled",show_alert=True)
        bot.send_message(call.message.chat.id,"Cancelled!")
        return

    winners=winner_state["winners"]
    g=load(FILES["giveaway"])

    txt="┌⚡──────────────────────────────────────────────⚡┐\n"
    txt+="🎉 POWER POINT BREAK — GIVEAWAY RESULT 🎉\n"
    txt+="└⚡──────────────────────────────────────────────⚡┘\n\n"

    for i,w in enumerate(winners,1):
        txt+=f"{i}) @{w['username']} | {w['id']}\n"

    txt+=f"\n🎁 Reward: {g['title']}\nHosted By: POWER POINT BREAK\nAdmin: @MinexxProo"

    try:
        bot.send_message(g["message_chat_id"],txt)
    except:
        bot.send_message(call.message.chat.id,txt)

    # Auto DM
    st=load(FILES["settings"])
    if st["auto_dm"]:
        for w in winners:
            try:
                bot.send_message(
                    w["id"],
                    "🎉 Congratulations!\nYou Won The Giveaway!\nContact @MinexxProo"
                )
            except:
                pass

    # Add to old winners
    old=set(g["old_winner_ids"])
    for w in winners:
        old.add(w["id"])
    g["old_winner_ids"]=list(old)
    save(FILES["giveaway"],g)

    bot.answer_callback_query(call.id,"Posted!",show_alert=True)
    winner_state["winners"]=[]

# =====================================================
# END GIVEAWAY
# =====================================================

@bot.message_handler(commands=['end'])
def end_cmd(msg):
    if msg.from_user.id!=ADMIN_ID:
        return

    g=load(FILES["giveaway"])
    g["active"]=False
    save(FILES["giveaway"],g)

    bot.reply_to(msg,"🛑 Giveaway Ended!\nUse /winner to select winner.")

# =====================================================
# BOT START
# =====================================================
print("BOT RUNNING...")
bot.infinity_polling()
