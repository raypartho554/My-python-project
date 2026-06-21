import telebot
import time
import hashlib  
import requests  # 🌐 লাইভ গেম API ফেচ করার জন্য
from datetime import datetime, timezone
from telebot import types

# 🛠️ আপনার দেওয়া অরিジナাল বোট টোকেন এবং অ্যাডমিন আইডি
API_TOKEN = '8439111290:AAHFZh92yYj8WUkJFJhX7898I6yqf0sflXI'
bot = telebot.TeleBot(API_TOKEN)

ADMIN_ID = 6104907925  

# 📢 আপনার দেওয়া সঠিক চ্যানেল আইডি ও লিংক
CHANNEL_ID = -1002942831211  
CHANNEL_LINK = 'https://t.me/+RYJ0isqB16UwZWJl'

# ডাটা ট্র্যাকিং
all_users = set()
banned_users = set()
requested_users = set()  
user_last_period = {}
username_to_id = {}

# আমাদের পাঠানো আগের প্রেডিকশন ট্র্যাক করার জন্য ডিকশনারি {period_number: predicted_result}
bot_predictions_history = {}

def get_period_and_timer():
    now = datetime.now(timezone.utc)
    seconds = now.second
    remaining_seconds = 60 - seconds
    minutes = now.minute
    hour_of_day = now.hour
    
    total_minutes = hour_of_day * 60 + minutes
    
    date_str = now.strftime("%Y%m%d")
    period_suffix = 10001 + total_minutes
    period_number = f"{date_str}1000{period_suffix}"
    
    return period_number, remaining_seconds

# 🌐 লাইভ গেম API থেকে শেষ রেজাল্ট ফেচ করার ফাংশন
def check_live_game_result(last_period):
    url = "https://api.bdg88zf.com/api/webapi/GetNoaverageEmerdList"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*"
    }
    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": 1, 
        "language": 0
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0 and data.get("data", {}).get("list"):
                game_list = data["data"]["list"]
                
                for game in game_list:
                    if str(game.get("issueNumber")) == str(last_period):
                        actual_number = int(game.get("number", -1))
                        
                        if actual_number >= 5:
                            return "BIG", actual_number
                        elif actual_number >= 0:
                            return "SMALL", actual_number
    except Exception as e:
        print(f"API Fetch Error: {e}")
        
    return None, None

# 🎯 ৩-ইন-১ হাইব্রিড প্রেডিকশন লজিক (বিপরীত নাম্বার জেনারেশন সহ)
def get_prediction_result(period_number):
    global bot_predictions_history
    
    try:
        last_period = str(int(period_number) - 1)
    except:
        last_period = None
        
    # --- লাইভ উইন/লস ডিটেকশন ---
    if last_period and last_period in bot_predictions_history:
        actual_result, actual_num = check_live_game_result(last_period)
        predicted_result = bot_predictions_history[last_period]
        
        if actual_result:
            if (predicted_result == "𝐁𝐈𝐆" and actual_result == "BIG") or \
               (predicted_result == "𝐒𝐌𝐀𝐋𝐋" and actual_result == "SMALL"):
                print(f"Period {last_period}: Bot WIN! 🎉")
            else:
                print(f"Period {last_period}: Bot LOSS! ❌")
    
    # --- SHA-256 Hash Algorithm (মেইন সিড জেনারেটর) ---
    secret_salt = "3_LEVEL_LIVE_API_SYSTEM_2026"
    data_to_hash = f"{period_number}-{secret_salt}"
    hash_object = hashlib.sha256(data_to_hash.encode())
    hash_hex = hash_object.hexdigest()
    hash_integer = int(hash_hex[:6], 16)
    
    # রেজাল্ট নির্ধারণ (BIG বা SMALL)
    trend_determiner = hash_integer % 2
    if trend_determiner == 0:
        base_choice = "𝐁𝐈𝐆"
    else:
        base_choice = "𝐒𝐌𝐀𝐋𝐋"
        
    if len(bot_predictions_history) > 20:
        bot_predictions_history.clear()
        
    bot_predictions_history[period_number] = base_choice
        
    # 🔥 বস, আপনার স্পেশাল বিপরীত (Opposite) নাম্বার লজিক এখানে দেওয়া হলো
    if base_choice == "𝐁𝐈𝐆":
        # রেজাল্ট BIG হলে নাম্বার আসবে SMALL (0,1,2,3,4) থেকে
        possible_nums = [0, 1, 2, 3, 4]
        idx1 = (hash_integer) % 5
        idx2 = (hash_integer + 2) % 5
        if idx1 == idx2:
            idx2 = (idx2 + 1) % 5
        num_list = [possible_nums[idx1], possible_nums[idx2]]
        num_list.sort()
        return "𝐁𝐈𝐆", f"{num_list[0]}.{num_list[1]}"
    else:
        # রেজাল্ট SMALL হলে নাম্বার আসবে BIG (5,6,7,8,9) থেকে
        possible_nums = [5, 6, 7, 8, 9]
        idx1 = (hash_integer) % 5
        idx2 = (hash_integer + 2) % 5
        if idx1 == idx2:
            idx2 = (idx2 + 1) % 5
        num_list = [possible_nums[idx1], possible_nums[idx2]]
        num_list.sort()
        return "𝐒𝐌𝐀𝐋𝐋", f"{num_list[0]}.{num_list[1]}"

# 📝 আপনার দেওয়া হুবহু সঠিক মেসেজ ফরম্যাট
def create_msg(period, result, nums):
    text = (
        f"√√𝙐𝙉𝘿𝙀𝙍 3 𝙇𝙀𝙑𝙀𝙇 𝙁𝙄𝙓𝙏 𝘽𝙊𝙏√√\n\n"
        f"⏰1 Mɪɴᴜᴛᴇ Pʀᴇᴅɪᴄᴛɪᴏɴ⏰\n\n"
        f"📊Pʀᴇɪᴏᴅ: {period}\n\n"
        f"🔮Rᴇsᴜʟᴛ: {result}➪{nums}\n\n"
        f"✉️𝙰𝙽𝚈 𝙿𝚁𝙾𝙱𝙻𝙴𝙼☟︎︎︎\n"
        f"𝙳𝙼:@PARTHO_THE_ONExx"
    )
    return text

def create_ban_msg():
    text = (
        f"❌ **ACCESS DENIED** ❌\n\n"
        f"🚫 **আপনাকে এই বোট থেকে ব্যান করা হয়েছে!**\n"
        f"আপনি আর কোনো প্রেডিকশন দেখতে পারবেন না।\n\n"
        f"💬 আনব্যান হতে বা যেকোনো প্রয়োজনে অ্যাডমিনের সাথে যোগাযোগ করুন:\n"
        f"👉 **DM:** @PARTHO_THE_ONExx"
    )
    return text

def register_user(user):
    all_users.add(user.id)
    if user.username:
        username_to_id[user.username.lower()] = user.id

# 🔐 চ্যানেল জয়েন চেক মেথড
def is_user_joined(user_id):
    if user_id in requested_users:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Membership Check Error: {e}")
        return False

@bot.chat_join_request_handler()
def handle_join_request(update):
    if update.chat.id == CHANNEL_ID:
        requested_users.add(update.from_user.id)

# --- 👑 ADMIN CONTROL PANEL 👑 ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_stats = types.InlineKeyboardButton("📊 View Stats & Users", callback_data="admin_stats")
        btn_help = types.InlineKeyboardButton("📢 Broadcast Guide", callback_data="admin_broadcast_guide")
        markup.add(btn_stats, btn_help)
        
        bot.send_message(message.chat.id, "👑 **Welcome Boss!**\nনিচের বাটন বা ইউজারনেম কমান্ড ব্যবহার করুন।\n\n📌 উদাহরণ: `/ban @username`\n📌 উদাহরণ: `/unban @username`", reply_markup=markup, parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ আপনি এই বোটের অ্যাডমিন নন!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_buttons(call):
    if call.from_user.id != ADMIN_ID:
        return
        
    if call.data == "admin_stats":
        total = len(all_users)
        banned = len(banned_users)
        stats_text = f"📊 **Current Bot Stats:**\n\n👥 Total Active Users: {total}\n🚫 Banned Users: {banned}"
        bot.send_message(call.message.chat.id, stats_text)
        bot.answer_callback_query(call.id)
        
    elif call.data == "admin_broadcast_guide":
        guide = (
            "📢 **স্মার্ট ব্রডকাস্ট গাইড:**\n\n"
            "১. **শুধু মেসেজ:** লিখুন `/broadcast আপনার মেসেজ`\n"
            "২. **ফাইল/ফটো:** ফাইল সেন্ড করার সময় ক্যাপশনে লিখে দিন `/broadcast`"
        )
        bot.send_message(call.message.chat.id, guide, parse_mode='Markdown')
        bot.answer_callback_query(call.id)

def execute_broadcast(message, text_to_send, content_type):
    success_count = 0
    bot.send_message(ADMIN_ID, f"📢 ব্রডকাস্ট শুরু হয়েছে... মোট ইউজার: {len(all_users)}")
    
    for user in list(all_users):
        if user not in banned_users:
            try:
                if content_type == 'text':
                    bot.send_message(user, text_to_send)
                elif content_type == 'photo':
                    bot.send_photo(user, message.photo[-1].file_id, caption=text_to_send)
                elif content_type == 'video':
                    bot.send_video(user, message.video.file_id, caption=text_to_send)
                elif content_type == 'document':
                    bot.send_document(user, message.document.file_id, caption=text_to_send)
                elif content_type == 'audio':
                    bot.send_audio(user, message.audio.file_id, caption=text_to_send)
                
                success_count += 1
                time.sleep(0.05)
            except Exception:
                all_users.remove(user)
                
    bot.send_message(ADMIN_ID, f"✅ ব্রডকাস্ট সম্পন্ন! সফল: {success_count} জন।")

@bot.message_handler(commands=['broadcast'])
def text_broadcast(message):
    if message.from_user.id == ADMIN_ID:
        msg_text = message.text.replace('/broadcast', '').strip()
        if not msg_text:
            bot.reply_to(message, "❌ প্লিজ মেসেজ লিখুন।", parse_mode='Markdown')
            return
        execute_broadcast(message, msg_text, 'text')

@bot.message_handler(content_types=['photo', 'video', 'document', 'audio'])
def media_broadcast(message):
    if message.from_user.id == ADMIN_ID:
        caption = message.caption if message.caption else ""
        if caption.startswith('/broadcast'):
            clean_caption = caption.replace('/broadcast', '').strip()
            execute_broadcast(message, clean_caption, message.content_type)

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id == ADMIN_ID:
        try:
            target = message.text.split()[1].replace('@', '').strip().lower()
            if target in username_to_id:
                target_id = username_to_id[target]
                banned_users.add(target_id)
                bot.reply_to(message, f"🚫 @{target} কে সফলভাবে ব্যান করা হয়েছে।")
            else:
                bot.reply_to(message, f"❌ দুঃখিত বস! @{target} নামের কোনো ইউজারকে বোট ট্র্যাক করতে পারেনি।")
        except IndexError:
            bot.reply_to(message, "❌ ব্যবহারের নিয়ম: `/ban @username`")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id == ADMIN_ID:
        try:
            target = message.text.split()[1].replace('@', '').strip().lower()
            if target in username_to_id:
                target_id = username_to_id[target]
                if target_id in banned_users:
                    banned_users.remove(target_id)
                    bot.reply_to(message, f"✅ @{target} কে আনব্যান করা হয়েছে।")
                else:
                    bot.reply_to(message, f"ℹ️ @{target} অলরেডি আনব্যান আছে।")
            else:
                bot.reply_to(message, f"❌ এই ইউজারনেমটি বোটের রেকর্ডে নেই।")
        except IndexError:
            bot.reply_to(message, "❌ ব্যবহারের নিয়ম: `/unban @username`")

# --- 🎮 USER ACTIONS 🎮 ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if user_id in banned_users:
        bot.send_message(message.chat.id, create_ban_msg(), parse_mode='Markdown')
        return
        
    register_user(message.from_user)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_join = types.InlineKeyboardButton("📢 Join Channel / Request", url=CHANNEL_LINK)
    btn_confirm = types.InlineKeyboardButton("✅ Confirm & Open Prediction", callback_data="check_join")
    markup.add(btn_join, btn_confirm)
    
    bot.send_message(
        message.chat.id, 
        "⚠️ **প্রেডিকশন পেজ ওপেন করতে প্রথমে নিচের বাটনে ক্লিক করে চ্যানেলে জয়েন রিকোয়েস্ট দিন!**\n\nরিকোয়েস্ট দেওয়ার পর নিচে **'✅ Confirm & Open Prediction'** বাটনে ক্লিক করুন।", 
        reply_markup=markup, 
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def handle_check_join(call):
    user_id = call.from_user.id
    
    if user_id in banned_users:
        bot.answer_callback_query(call.id, text="🚫 আপনি ব্যান আছেন!", show_alert=True)
        return

    if is_user_joined(user_id):
        bot.answer_callback_query(call.id, text="✅ ভেরিফিকেশন সফল! প্রেডিকশন পেজ ওপেন হচ্ছে...", show_alert=True)
        try:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass
            
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("🔄 /NEXT PREDICTION", callback_data="next_prediction")
        markup.add(btn)
        
        welcome_text = "🤖 বোট রেডি আছে বস! নিচের বাটনে ক্লিক করে প্রেডিকশন নিন।"
        bot.send_message(call.message.chat.id, welcome_text, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, text="❌ আপনি এখনও জয়েন রিকোয়েস্ট দেননি! দয়া করে বাটনে ক্লিক করে রিকোয়েস্ট পাঠান।", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "next_prediction")
def handle_next_prediction(call):
    user_id = call.from_user.id
    
    if user_id in banned_users:
        bot.answer_callback_query(call.id, text="🚫 আপনি ব্যান আছেন!", show_alert=True)
        bot.send_message(call.message.chat.id, create_ban_msg(), parse_mode='Markdown')
        return
        
    if not is_user_joined(user_id):
        bot.answer_callback_query(call.id, text="⚠️ প্রেডিকশন দেখতে আপনাকে অবশ্যই চ্যানেলে থাকতে হবে!", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_join = types.InlineKeyboardButton("📢 Join Channel / Request", url=CHANNEL_LINK)
        btn_confirm = types.InlineKeyboardButton("✅ Confirm & Open Prediction", callback_data="check_join")
        markup.add(btn_join, btn_confirm)
        bot.send_message(call.message.chat.id, "⚠️ **চ্যানেল থেকে রিকোয়েস্ট লিভ করেছেন! আবার রিকোয়েস্ট দিন:**", reply_markup=markup)
        return
        
    register_user(call.from_user)
    current_period, remaining_seconds = get_period_and_timer()
    
    if user_id in user_last_period and user_last_period[user_id] == current_period:
        alert_msg = f"⏳ ওয়েট করুন বস! এই পিরিয়ডের সময় শেষ হতে আরও {remaining_seconds} সেকেন্ড বাকি।"
        bot.answer_callback_query(call.id, text=alert_msg, show_alert=True)
    else:
        user_last_period[user_id] = current_period
        
        result, nums = get_prediction_result(current_period)  
        
        if "বোট রেডি আছে বস" in call.message.text:
            try:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            except Exception:
                pass
        else:
            try:
                bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            except Exception:
                pass
        
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("🔄 /NEXT PREDICTION", callback_data="next_prediction")
        markup.add(btn)
        
        bot.send_message(call.message.chat.id, create_msg(current_period, result, nums), reply_markup=markup)
        bot.answer_callback_query(call.id)

print("Your opposite number hybrid bot is running...")
bot.infinity_polling()
