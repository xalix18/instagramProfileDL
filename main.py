from instagrapi import Client
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
import re
import logging

# فعال کردن لاگ
logging.basicConfig(level=logging.INFO)


# تلگرام
TOKEN = "7979842928:AAE0iRK0pDSbIMr18h8kmkQbbQm37lY3xzc"

# اینستا
cl = Client()
cl.login("alialialimkg","ali@1384")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ربات دانلود عکس پروفایل اینستاگرام هستم.\n"
        "فقط کافیه یوزرنیم یا لینک پروفایل اینستا رو برام بفرستی."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    
    # پرینت پیام دریافتی در کنسول
    print(f"[INFO] Received message: {user_message}")

    # استخراج یوزرنیم از لینک یا متن
    username = None
    url_match = re.search(r"instagram\.com/([a-zA-Z0-9_.]+)", user_message)
    if url_match:
        username = url_match.group(1)
    elif re.match(r"^[a-zA-Z0-9_.]+$", user_message):
        username = user_message

    if not username:
        await update.message.reply_text("❌ لطفاً یک یوزرنیم یا لینک اینستاگرام معتبر ارسال کن.")
        return

    # ریپلای اولیه
    await update.message.reply_text("⏳ لطفاً صبر کنید… در حال دریافت پروفایل")

    try:
        user_id = cl.user_id_from_username(username)
        info = cl.user_info(user_id)

        profile_pic_url = str(info.profile_pic_url_hd)

        # آماده‌سازی اطلاعات پروفایل
        full_name = info.full_name or "—"
        biography = info.biography or "—"
        followers = info.follower_count
        followees = info.following_count
        posts = info.media_count
        is_private = "بله" if info.is_private else "خیر"
        is_verified = "بله" if info.is_verified else "خیر"

        # کپشن امن
        caption = (
            f"*👤 نام کاربری:* {escape_markdown(username, version=2)}\n"
            f"*📝 نام کامل:* {escape_markdown(full_name, version=2)}\n"
            f"*👥 فالوورها:* {escape_markdown(f'{followers:,}', version=2)}\n"
            f"*👀 فالویینگ‌ها:* {escape_markdown(f'{followees:,}', version=2)}\n"
            f"*🖼️ تعداد پست‌ها:* {escape_markdown(f'{posts:,}', version=2)}\n"
            f"*🔒 خصوصی:* {escape_markdown(is_private, version=2)}\n"
            f"*✔️ تیک آبی:* {escape_markdown(is_verified, version=2)}\n\n"
            f"*ℹ️ بیوگرافی:*\n{escape_markdown(biography, version=2)}"
        )

        # ارسال عکس با کپشن کامل
        await update.message.reply_photo(
            photo=profile_pic_url,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN_V2
        )

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا: {e}")
        logging.error(f"Error fetching profile for {username}: {e}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
