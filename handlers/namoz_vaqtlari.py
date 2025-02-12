#namoz vaqtlari handler
import requests
import telebot

from telebot import types
from handlers.config import TOKEN,CHANNEL_ID

ADMIN_ID = [6870812534]
bot = telebot.TeleBot(TOKEN)


# Function to fetch and send prayer times to the channel
def send_weekly_calendar(message):
    try:
        city = "Buxoro"
        url = f"https://islomapi.uz/api/present/week?region={city}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data:
                message_content = f"{city} viloyati uchun haftalik namoz vaqtlari:\n\n"

                weekdays = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"]

                for day_data in data:
                    date = day_data['date'].split(",")[0]
                    weekday = day_data['weekday']

                    names = {
                        "tong_saharlik": "Bomdod",
                        "quyosh": "Quyosh",
                        "peshin": "Peshin",
                        "asr": "Asr",
                        "shom_iftor": "Shom",
                        "hufton": "Xufton"
                    }

                    message_content += f"{weekday}, {date}:\n"
                    for key, value in day_data['times'].items():
                        if key in names:
                            message_content += f"{names[key]}: {value}\n"
                    
                    message_content += "\n"

                # Rasm URL manzili
                photo_url = "https://namozvaqti.uz/img/logo_new.png"
                
                # Send the prayer times to the channel
                bot.send_photo(CHANNEL_ID, photo_url, caption=message_content)
                
                # Send a confirmation message to admins
                for admin_id in ADMIN_ID:
                    bot.send_message(admin_id, "Haftalik namoz vaqtlari va rasm kanalga yuborildi!")
            else:
                # Handle case where no data is received
                for admin_id in ADMIN_ID:
                    bot.send_message(admin_id, "Haftalik namoz vaqtlari topilmadi")
        else:
            # Handle case where API request fails
            for admin_id in ADMIN_ID:
                bot.send_message(admin_id, "Serverdan ma'lumotlar olinmadi")
    except Exception as e:
        # Handle any other errors
        for admin_id in ADMIN_ID:
            bot.send_message(admin_id, f"Xatolik yuzaga keldi: {e}")

# Command to trigger prayer times sending to channel and notify user
@bot.message_handler(commands=['calendar'])
def handle_calendar_command(message):
    send_weekly_calendar(message)
    bot.send_message(message.chat.id, "Namoz vaqtlari kanalga yuborildi!")

# Callback for any further interaction if needed
@bot.callback_query_handler(func=lambda call: call.data == "send_calendar")
def send_calendar_callback(call):
    send_weekly_calendar(call.message)
    bot.send_message(call.message.chat.id, "Namoz vaqtlari kanalga yuborildi!")

