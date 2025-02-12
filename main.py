import telebot
import instaloader
import time
import os

from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.namoz_vaqtlari import send_weekly_calendar
from handlers.config import TOKEN, CHANNEL_ID, ADMIN_ID, ADMIN_IDs
from handlers.db import cursor,conn  

bot = TeleBot(TOKEN)
loader = instaloader.Instaloader()


# SQLite3 bazasi bilan ulanish va jadval yaratish
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    # Foydalanuvchi ma'lumotlarini bazaga saqlash
    cursor.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()

    if result is None:
        # Foydalanuvchini bazaga qo'shish
        cursor.execute('INSERT INTO users (chat_id, first_name, last_name, username) VALUES (?, ?, ?, ?)', 
                       (chat_id, first_name, last_name, username))
        conn.commit()
        
    bot.reply_to(message, "Salom! Bot yordamida @Amor_Fati_dunya Kanaliga oʻzingizga yoqqan vedioni joylashtrishingiz mumkin! /help")

  # Tugmalar yaratish
    keyboard = types.InlineKeyboardMarkup()
    # Agar foydalanuvchi admin bo‘lsa, qo‘shimcha tugma qo‘shiladi
    if chat_id in ADMIN_IDs:
        keyboard.add(types.InlineKeyboardButton("🕌 Namoz vaqtlari", callback_data="send_calendar"))

    bot.send_message(chat_id, "📥 Instagram post yoki Reels havolasini yuboring, men esa uni yuklab beraman. 📥", reply_markup=keyboard)

# Command to trigger the calendar
@bot.message_handler(commands=['calendar'])
def handle_calendar_command(message):
    send_weekly_calendar(message)

# Callback function to handle custom callback for sending calendar
@bot.callback_query_handler(func=lambda call: call.data == "send_calendar")
def send_calendar_callback(call):
    send_weekly_calendar(call.message)
    # Send confirmation message about prayer times (namoz vaqtlari)
    bot.send_message(call.message.chat.id, "Namoz vaqtlari yuborildi")


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """🤖 *Botdan foydalanish bo‘yicha yordam:*

📝 *Foydalanuvchilar uchun:*
- 📥 *Instagram post yoki Reels yuklash:* Linkni yuboring, men esa uni yuklab beraman.

📩 Qo‘shimcha yordam kerak bo‘lsa, admin bilan bog‘laning.

🔹 *Botni yaratgan:* [Admin](https://t.me/Izzatbek_Ibrohimov)
"""
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['admin'])
def send_admin_commands(message):
    # Adminlarning chat_id'larini ro‘yxatini tekshirish
    if message.chat.id not in ADMIN_IDs:
        bot.send_message(message.chat.id, "⚠️ Siz admin emassiz. Bu buyruq faqat admin uchun mavjud.")
        return

    admin_commands = """👑 <b>Admin buyruqlari:</b>

- 📜 <i>Foydalanuvchilar ro‘yxatini ko‘rish:</i> /users_list

🛠 Yordam uchun boshqa buyruqlarni /help komandasidan topishingiz mumkin.
"""
    try:
        # HTML formatida xabar yuborish
        bot.send_message(message.chat.id, admin_commands, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        # Xatolik yuz berganda to‘g‘ridan-to‘g‘ri habar yuboring
        bot.send_message(message.chat.id, f"Xatolik yuz berdi: {e}")
        
# /users_list buyrug'ini qabul qilish
@bot.message_handler(commands=['users_list'])
def send_users_list(message):
    if message.chat.id == ADMIN_ID:  # Faqat admin uchun
        cursor.execute("SELECT chat_id, first_name, last_name, username FROM users")
        users = cursor.fetchall()

        if users:
            user_list = "👤 <b>Foydalanuvchilar ro‘yxati:</b>\n\n"
            for user in users:
                chat_id, first_name, last_name, username = user
                username = f"@{username}" if username else "Yo‘q"

                # Stiker va emoji noto‘g‘ri ishlashining oldini olish
                first_name = first_name or ""
                last_name = last_name or ""

                user_list += f"📌 <b>Chat ID:</b> <code>{chat_id}</code>\n👤 <b>Ism:</b> {first_name} {last_name}\n🆔 <b>Username:</b> {username}\n\n"
            
            bot.send_message(message.chat.id, user_list, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "🛑 Hech qanday foydalanuvchi topilmadi.")
    else:
        bot.send_message(message.chat.id, "⛔ Sizda bu buyruqdan foydalanish huquqi yo‘q.")

        
def clear_downloads():
    """Yuklab bo‘lgach, barcha fayllarni tozalaydi."""
    for file in os.listdir("downloads"):
        os.remove(f"downloads/{file}")

def send_progress_message(chat_id):
    """Yuklash jarayonida foydalanuvchiga progress ko‘rsatish."""
    msg = bot.send_message(chat_id, "⏳ Yuklanmoqda")
    for i in range(3):  
        time.sleep(1)
        bot.edit_message_text(f"⏳ Yuklanmoqda{'.' * (i % 3 + 1)}", chat_id, msg.message_id)
    return msg

@bot.message_handler(func=lambda message: message.text.startswith("https://www.instagram.com/"))
def download_instagram_media(message):
    url = message.text
    progress_msg = send_progress_message(message.chat.id)
    
    try:
        short_code = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, short_code)
        loader.download_post(post, target="downloads")
        
        video_sent = False
        for file in os.listdir("downloads"):
            file_path = f"downloads/{file}"
            if file.endswith(".mp4"):
                with open(file_path, "rb") as vid:
                    sent_message = bot.send_video(message.chat.id, vid)
                    video_sent = True
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("📤 Kanalga yuborish", callback_data=f"send_to_admin|{sent_message.message_id}|{message.chat.id}"))
                bot.send_message(message.chat.id, "📢 Videoni kanalga yuborish\nuchun tugmani bosing:", reply_markup=markup)

        bot.delete_message(message.chat.id, progress_msg.message_id)
        
        if not video_sent:
            bot.send_message(message.chat.id, "⚠️ Video topilmadi yoki yuklab bo‘lmadi.")

        clear_downloads()
        
    except Exception as e:
        bot.edit_message_text("⚠️ Yuklashda xatolik yuz berdi!", message.chat.id, progress_msg.message_id)
        print(e)

@bot.callback_query_handler(func=lambda call: call.data.startswith("send_to_admin"))
def send_to_admin(call):
    _, message_id, user_chat_id = call.data.split("|")
    forwarded_message = bot.forward_message(ADMIN_ID, user_chat_id, message_id)
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Ha", callback_data=f"approve_yes|{forwarded_message.message_id}|{user_chat_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"approve_no|{forwarded_message.message_id}|{user_chat_id}")
    )
    
    bot.send_message(ADMIN_ID, "🔹 Ushbu videoni kanalga yuboramizmi?", reply_markup=markup)
    bot.answer_callback_query(call.id, "✅ Video adminlarga yuborildi!")
    bot.send_message(call.message.chat.id, "✅ Video adminlarga yuborildi!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def handle_approval(call):
    action, message_id, user_chat_id = call.data.split("|")
    
    if action == "approve_yes":
        bot.copy_message(CHANNEL_ID, ADMIN_ID, message_id, caption="Amor Fati 🤍\n@Amor_Fati_dunya")
        bot.send_message(ADMIN_ID, "📢 Video kanalga yuborildi!")
        bot.send_message(user_chat_id, "✅ Videongiz uchun rahmat! Kanalga yuklandi. 🎉")
    else:
        bot.send_message(ADMIN_ID, "🚫 Video kanalga yuborilmadi.")
        bot.send_message(user_chat_id, "❌ Kechirasiz, videongiz kanalga yuklanmadi.")

    bot.answer_callback_query(call.id)

#vedio va rasmni tasdiqlash

media_messages = {}  # Foydalanuvchining media xabarlari saqlanadigan joy

@bot.message_handler(content_types=['photo', 'video'])
def receive_media(message):
    """Foydalanuvchidan media qabul qilish, adminga yuborish va unga bildirish berish."""
    msg = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

    # Foydalanuvchiga bildirish
    bot.send_message(message.chat.id, "📩 Xabaringiz adminga yuborildi, javobini kuting.")

    # Admin uchun inline tugmalar
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"approve_{message.chat.id}_{msg.message_id}"),
        InlineKeyboardButton("❌ Yo‘q", callback_data=f"reject_{message.chat.id}")
    )

    bot.send_message(ADMIN_ID, "📩 Ushbu media tasdiqlansinmi?", reply_markup=markup, reply_to_message_id=msg.message_id)

    # Xabar ma'lumotlarini saqlash
    media_messages[msg.message_id] = {
        "user_id": message.chat.id,
        "message_id": message.message_id
    }

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_admin_response(call):
    """Admin 'Ha' yoki 'Yo‘q' tugmalarini bosganda ishlaydi."""
    data = call.data.split("_")
    action = data[0]
    user_id = int(data[1])
    admin_message_id = int(call.message.reply_to_message.message_id)

    if admin_message_id in media_messages:
        msg_data = media_messages[admin_message_id]

        if action == "approve":
            bot.copy_message(
                CHANNEL_ID, ADMIN_ID, admin_message_id, caption="Amor Fati"
            )
            bot.send_message(user_id, "✅ Rasm yoki video uchun rahmat! Kanaldan ko‘rishingiz mumkin.")
        elif action == "reject":
            bot.send_message(user_id, "❌ Sizning rasmingiz yoki videongiz rad etildi.")

        del media_messages[admin_message_id]  # Xotiradan o‘chirish

    bot.answer_callback_query(call.id, "Tanlov qabul qilindi.")

# Xatolikni adminlarga yuborish funksiyasi
def notify_admins_about_error(e):
    for admin_id in ADMIN_IDs:
        try:
            bot.send_message(admin_id, f"Botda xatolik yuz berdi: {e}")
        except Exception as notify_error:
            print(f"Adminlarga xabar yuborishda xatolik: {notify_error}")


# Botni qayta ishga tushirish sikli
while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Xato sodir bo'ldi: {e}")
        notify_admins_about_error(e)  # Xatolikni adminlarga yuborish
        time.sleep(5)  # 5 soniya kutib qayta urinish