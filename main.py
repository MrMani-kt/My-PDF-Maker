import telebot
from telebot import types
import img2pdf
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import threading
import time
import config

bot = telebot.TeleBot(config.TOKEN)


user_data = {}

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn_text = types.InlineKeyboardButton("📝 تبدیل متن به PDF", callback_data="convert_text")
    btn_album = types.InlineKeyboardButton("📚 ساخت پی‌دی‌اف از عکس‌ها", callback_data="make_album")
    btn_clear = types.InlineKeyboardButton("🗑 خالی کردن لیست عکس‌ها", callback_data="clear_list")
    markup.add(btn_text)
    markup.add(btn_album)
    markup.add(btn_clear)
    return markup

@bot.message_handler(commands=['start', 'help'])
def start(message):
    user_data[message.chat.id] = {'images': [], 'waiting_for_text': False}
    bot.send_message(message.chat.id, 
                     "سلام! به ربات مبدل خوش آمدید.\n\n"
                     "• عکس‌ها را (چه معمولی چه فایل) بفرستید تا به لیست اضافه شوند.\n"
                     "• سپس روی دکمه 'ساخت پی‌دی‌اف' بزنید.", 
                     reply_markup=get_main_keyboard())


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_id = message.photo[-1].file_id
    save_image(message, file_id)


@bot.message_handler(content_types=['document'])
def handle_document(message):

    if message.document.mime_type.startswith('image/'):
        file_id = message.document.file_id
        save_image(message, file_id)
    else:
        bot.reply_to(message, "لطفاً فقط فایل تصویری بفرستید.")

def save_image(message, file_id):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {'images': [], 'waiting_for_text': False}
    
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    file_name = f"img_{chat_id}_{len(user_data[chat_id]['images'])}.jpg"
    with open(file_name, 'wb') as f:
        f.write(downloaded_file)
    
    user_data[chat_id]['images'].append(file_name)
    bot.reply_to(message, f"✅ عکس شماره {len(user_data[chat_id]['images'])} دریافت شد.")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "make_album":
        if chat_id in user_data and user_data[chat_id]['images']:
            bot.answer_callback_query(call.id, "در حال ساخت PDF...")
            pdf_name = f"album_{chat_id}.pdf"
            
            with open(pdf_name, "wb") as f:
                f.write(img2pdf.convert(user_data[chat_id]['images']))
            
            with open(pdf_name, 'rb') as f:
                bot.send_document(chat_id, f, caption="📚 آلبوم تصاویر شما آماده شد.")
            

            for img in user_data[chat_id]['images']:
                os.remove(img)
            os.remove(pdf_name)
            user_data[chat_id]['images'] = []
        else:
            bot.answer_callback_query(call.id, "ابتدا چند عکس بفرستید!", show_alert=True)

    elif call.data == "convert_text":
        user_data[chat_id]['waiting_for_text'] = True
        bot.send_message(chat_id, "لطفاً متنی که می‌خواهید به PDF تبدیل شود را تایپ کنید:")

    elif call.data == "clear_list":
        if chat_id in user_data:
            for img in user_data[chat_id]['images']:
                if os.path.exists(img): os.remove(img)
            user_data[chat_id]['images'] = []
            bot.answer_callback_query(call.id, "لیست پاک شد.")


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    if chat_id in user_data and user_data[chat_id].get('waiting_for_text'):
        pdf_name = f"text_{chat_id}.pdf"
        

        c = canvas.Canvas(pdf_name, pagesize=letter)
        c.setFont("Helvetica", 12)

        c.drawString(100, 750, message.text)
        c.save()
        
        with open(pdf_name, 'rb') as f:
            bot.send_document(chat_id, f, caption="📝 فایل متنی شما آماده شد.")
        
        os.remove(pdf_name)
        user_data[chat_id]['waiting_for_text'] = False
    else:
        bot.reply_to(message, "لطفاً از دکمه‌ها استفاده کنید یا عکس بفرستید.")

def delete_file_after_delay(file_path, delay=30):
    """تابعی برای پاک کردن فایل پس از مدتی مشخص"""
    def task():
        time.sleep(delay)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑 فایل {file_path} جهت بهینه‌سازی دیتابیس پاک شد.")
            

    threading.Thread(target=task).start()


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "make_album":
        if chat_id in user_data and user_data[chat_id]['images']:
            pdf_name = f"album_{chat_id}.pdf"
            

            with open(pdf_name, "wb") as f:
                f.write(img2pdf.convert(user_data[chat_id]['images']))
            

            with open(pdf_name, 'rb') as f:
                bot.send_document(
                    chat_id, 
                    f, 
                    caption="📚 آلبوم شما آماده شد.\n⚠️ این فایل جهت حفظ فضای دیتابیس، ۳۰ ثانیه دیگر از سرور حذف می‌شود."
                )
            

            for img in user_data[chat_id]['images']:
                if os.path.exists(img): os.remove(img)
            user_data[chat_id]['images'] = []


            delete_file_after_delay(pdf_name, 30)
            
        else:
            bot.answer_callback_query(call.id, "لیست عکس‌های شما خالی است!", show_alert=True)




bot.infinity_polling()




