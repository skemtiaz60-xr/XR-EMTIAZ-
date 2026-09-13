import logging
import uuid
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ----------------- 1. Web Server Setup (Replit-এ 24/7 অন রাখার জন্য) -----------------
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is online 24/7!")

def run_web_server():
    server = HTTPServer(('0.0.0.0', 8080), KeepAliveHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# ----------------- 2. Bot Configuration -----------------
BOT_TOKEN = "8991288434:AAFO_iVS6VR0alh9zWZkK15oIwikjeO2cLE"

# আপনার চ্যানেলসমূহের তথ্য
CHANNEL_1 = "@Earning_emtiaz_xr"
CHANNEL_2 = "@xremtiazgaming"

CHANNEL_1_LINK = "https://t.me/Earning_emtiaz_xr" 
CHANNEL_2_LINK = "https://t.me/xremtiazgaming"

# আপনার দেওয়া ভিডিওর ডাইরেক্ট লিঙ্ক
VIDEO_URL = "https://videotourl.com/videos/edddcad8-bc57-4b8e-bd6f-b3143fe28f23.mp4"

file_db = {}

# ইউজার ২টি চ্যানেলে জয়েন আছে কিনা তা চেক করার ফাংশন
async def is_user_subscribed(bot, user_id):
    try:
        member1 = await bot.get_chat_member(chat_id=CHANNEL_1, user_id=user_id)
        member2 = await bot.get_chat_member(chat_id=CHANNEL_2, user_id=user_id)
        
        valid_status = ['creator', 'administrator', 'member']
        if member1.status in valid_status and member2.status in valid_status:
            return True
        return False
    except Exception as e:
        print(f"Subscription Check Error: {e}")
        return False

# জয়েন বাটন লেআউট
def get_join_keyboard(file_key=""):
    keyboard = [
        [InlineKeyboardButton("🌸 📢 JOIN CHANNEL 1 🌸", url=CHANNEL_1_LINK)],
        [InlineKeyboardButton("🌸 📢 JOIN CHANNEL 2 🌸", url=CHANNEL_2_LINK)],
        [InlineKeyboardButton("🌸 🟢 VERIFY 🌸", callback_data=f"verify_{file_key}")]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    file_key = args[0] if args else ""

    subscribed = await is_user_subscribed(context.bot, user_id)

    if not subscribed:
        caption_text = (
            "╔═══════════════════════╗\n"
            "   🌸 **JOIN ALL CHANNELS** 🌸\n"
            "╚═══════════════════════╝\n\n"
            "🌺 **ফাইল ডাউনলোড করতে সব চ্যানেলে জয়েন করা বাধ্যতামূলক** 🌺\n\n"
            "নিচের চ্যানেল দুটিতে জয়েন করে **VERIFY** বাটনে চাপ দিন।"
        )
        
        # ভিডিও সহ জয়েন মেসেজ
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=VIDEO_URL,
            caption=caption_text,
            reply_markup=get_join_keyboard(file_key),
            parse_mode="Markdown"
        )
    else:
        await deliver_file(update.message, context, file_key)

# VERIFY বাটনে ক্লিক হ্যান্ডলার
async def verify_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    file_key = query.data.replace("verify_", "")

    subscribed = await is_user_subscribed(context.bot, user_id)

    if subscribed:
        await query.message.delete()
        await deliver_file(query.message, context, file_key)
    else:
        await query.answer("❌ আপনি এখনও সব চ্যানেলে জয়েন করেননি! আগে ২টা চ্যানেলেই জয়েন করুন।", show_alert=True)

# ফাইল ডেলিভারি ফাংশন
async def deliver_file(message, context, file_key):
    if file_key and file_key in file_db:
        file_info = file_db[file_key]
        await context.bot.send_message(chat_id=message.chat_id, text="📦 **আপনার ফাইল প্রস্তুত হচ্ছে...**", parse_mode="Markdown")
        await context.bot.send_document(
            chat_id=message.chat_id,
            document=file_info["file_id"],
            caption=f"✅ **{file_info['file_name']}**\n\nMY MODS Store"
        )
    else:
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="👋 **Welcome to MY MODS Store Bot!**\n\nআপনি সফলতা সহকারে ভেরিফাই করেছেন। ওয়েবসাইট থেকে অ্যাপ ডাউনলোড করতে ডাউনলোডের লিংকে ক্লিক করুন।",
            parse_mode="Markdown"
        )

# ফাইল আপলোড করা হলে ডাউনলোড লিংক তৈরি
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file_id = document.file_id
    file_name = document.file_name
    
    unique_key = f"file_{uuid.uuid4().hex[:6]}"
    file_db[unique_key] = {"file_id": file_id, "file_name": file_name}
    
    bot_info = await context.bot.get_me()
    deep_link = f"https://t.me/{bot_info.username}?start={unique_key}"
    
    await update.message.reply_text(
        f"✅ **ফাইল লিংক তৈরি হয়েছে!**\n\n"
        f"📁 **নাম:** `{file_name}`\n"
        f"🔗 **লিংক:** `{deep_link}`\n\n"
        f"👉 এই লিংকটি আপনার admin.html-এ ডাউনলোড লিংক হিসেবে বসান।",
        parse_mode="Markdown"
    )

def main():
    print("Bot starting with Video, 24/7 web server & Force-Sub check...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_click, pattern="^verify_"))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("Bot is Live 24/7!")
    app.run_polling()

if __name__ == "__main__":
    main()
