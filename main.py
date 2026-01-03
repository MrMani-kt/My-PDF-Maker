import telebot
from telebot import types
import img2pdf
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import threading
import time
import config 

bot = telebot.TeleBot(config.TOKEN)

# دیتابیس موقت برای ذخیره وضعیت کاربران
user_data = {}

# ثبت فونت فارسی برای PDF
try:
    pdfmetrics.registerFont(TTFont('PersianFont', 'Vazir.TTF'))
except Exception as e:
    print(f"⚠️ هشدار: فایل فونت پیدا نشد. متن‌های فارسی ممکن است خراب شوند. خطا: {e}")

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📝 تبدیل متن به PDF", callback_data="convert_text"))
    markup.add(types.InlineKeyboardButton("📚 ساخت پی‌دی‌اف از عکس‌ها", callback_data="make_album"))
    markup.add(types.InlineKeyboardButton("🗑 خالی کردن لیست عکس‌ها", callback_data="clear_list"))
    return markup

def delete_file_after_delay(file_path, delay=30):
    """پاکسازی فایل‌ها از سرور برای بهینه‌سازی فضا"""
    def task():
        time.sleep(delay)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑 فایل {file_path} پاک شد.")
    threading.Thread(target=task).start()

@bot.message_handler(commands=['start', 'help'])
def start(message):
    user_data[message.chat.id] = {'images': [], 'waiting_for_text': False}
    bot.send_message(message.chat.id, 
                     "سلام! به ربات مبدل خوش آمدید.\n\n"
                     "• عکس‌ها را بفرستید تا لیست شوند.\n"
                     "• سپس روی دکمه 'ساخت پی‌دی‌اف' بزنید.", 
                     reply_markup=get_main_keyboard())

@bot.message_handler(content_types=['photo', 'document'])
def handle_incoming_files(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {'images': [], 'waiting_for_text': False}

    file_id = None
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type.startswith('image/'):
        file_id = message.document.file_id

    if file_id:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = f"img_{chat_id}_{len(user_data[chat_id]['images'])}.jpg"
        with open(file_name, 'wb') as f:
            f.write(downloaded_file)
        user_data[chat_id]['images'].append(file_name)
        bot.reply_to(message, f"✅ عکس شماره {len(user_data[chat_id]['images'])} دریافت شد.")
    else:
        bot.reply_to(message, "لطفاً فقط فایل تصویری بفرستید.")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {'images': [], 'waiting_for_text': False}

    if call.data == "make_album":
        if user_data[chat_id]['images']:
            bot.answer_callback_query(call.id, "در حال ساخت PDF...")
            pdf_name = f"album_{chat_id}.pdf"
            try:
                with open(pdf_name, "wb") as f:
                    f.write(img2pdf.convert(user_data[chat_id]['images']))
                
                with open(pdf_name, 'rb') as f:
                    bot.send_document(chat_id, f, caption="📚 آلبوم شما آماده شد.")
                
                # پاکسازی تصاویر بلافاصله
                for img in user_data[chat_id]['images']:
                    if os.path.exists(img): os.remove(img)
                user_data[chat_id]['images'] = []
                
                # پاکسازی فایل PDF بعد از ۳۰ ثانیه
                delete_file_after_delay(pdf_name, 30)
            except Exception as e:
                bot.send_message(chat_id, f"خطا در ساخت PDF: {e}")
        else:
            bot.answer_callback_query(call.id, "ابتدا عکس بفرستید!", show_alert=True)

    elif call.data == "convert_text":
        user_data[chat_id]['waiting_for_text'] = True
        bot.send_message(chat_id, "لطفاً متن خود را (فارسی یا انگلیسی) بفرستید:")

    elif call.data == "clear_list":
        for img in user_data[chat_id]['images']:
            if os.path.exists(img): os.remove(img)
        user_data[chat_id]['images'] = []
        bot.answer_callback_query(call.id, "لیست با موفقیت پاک شد.")

@bot.message_handler(func=lambda message: True)
def handle_all_text(message):
    chat_id = message.chat.id
    if chat_id in user_data and user_data[chat_id].get('waiting_for_text'):
        pdf_name = f"text_{chat_id}.pdf"
        try:
            # آماده‌سازی متن برای زبان فارسی (راست‌چین و چسباندن حروف)
            reshaped_text = reshape(message.text)
            bidi_text = get_display(reshaped_text)

            c = canvas.Canvas(pdf_name, pagesize=letter)
            c.setFont("PersianFont", 12)
            c.drawRightString(550, 750, bidi_text) # نوشتن از سمت راست
            c.save()

            with open(pdf_name, 'rb') as f:
                bot.send_document(chat_id, f, caption="📝 فایل متنی شما آماده شد.")
            
            delete_file_after_delay(pdf_name, 5)
            user_data[chat_id]['waiting_for_text'] = False
        except Exception as e:
            bot.reply_to(message, f"خطا در تبدیل متن: {e}")
    else:
        bot.reply_to(message, "لطفاً از منوی دکمه‌ها استفاده کنید.")

print("--- ربات با تمام قابلیت‌ها فعال شد ---")
bot.infinity_polling()




