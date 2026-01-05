import telebot
from telebot import types
import config  

bot = telebot.TeleBot(config.TOKEN)

# تابع ساخت منوی اصلی شیشه‌ای
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_text_to_pdf = types.InlineKeyboardButton("📝 متن به PDF", callback_data="improve")
    btn_img_to_pdf = types.InlineKeyboardButton("🖼️ عکس به PDF", callback_data="improve")
    btn_merge_pdf = types.InlineKeyboardButton("📄 ادغام PDFها", callback_data="improve")
    btn_help = types.InlineKeyboardButton("❓ راهنما", callback_data="improve")
    
    markup.add(btn_text_to_pdf, btn_img_to_pdf, btn_merge_pdf, btn_help)
    return markup

# مدیریت دستور /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "سلام! به ربات PDF ساز خوش آمدید.\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

# مدیریت کلیک بر روی دکمه‌های شیشه‌ای
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "improve":
        bot.answer_callback_query(call.id) # برای غیب شدن ساعتک روی دکمه
        bot.send_message(call.message.chat.id, "🛠 این بخش هنوز در حال بهبود و توسعه است. به زودی فعال می‌شود!")

if __name__ == "__main__":
    print("--- ربات فقط با منوی شیشه‌ای فعال شد ---")
    bot.infinity_polling()




