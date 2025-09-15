import os
import logging
import re
import base64
from instagrapi import Client
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

# ---------- logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------- env vars ----------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
IG_USERNAME = os.environ.get("IG_USERNAME")
IG_PASSWORD = os.environ.get("IG_PASSWORD")

# فایل سشن/ستینگ اینستا روی دیسک (اختیاری)
SESSION_FILE = os.environ.get("IG_SESSION_FILE", "ig_session.json")
# اگر فایل سشن رو به صورت base64 توی متغیر محیطی گذاشتی:
IG_SESSION_B64 = os.environ.get("IG_SESSION_BASE64")

# اعتبارسنجی اولیه
if not TELEGRAM_TOKEN or not IG_USERNAME or not IG_PASSWORD:
    logger.error("Missing one of required env vars: TELEGRAM_TOKEN, IG_USERNAME, IG_PASSWORD")
    raise SystemExit("Set TELEGRAM_TOKEN, IG_USERNAME and IG_PASSWORD as environment variables")

# ---------- Prepare Instagram client ----------
cl = Client()

# اگر متغیر base64 سشن داده شده -> بازسازی فایل سشن
if IG_SESSION_B64:
    try:
        with open(SESSION_FILE, "wb") as f:
            f.write(base64.b64decode(IG_SESSION_B64))
        logger.info("Wrote IG session from IG_SESSION_BASE64 to %s", SESSION_FILE)
        # try load settings if client supports load_settings
        try:
            cl.load_settings(SESSION_FILE)
            logger.info("Loaded IG settings from file")
        except Exception:
            logger.info("load_settings not available or failed; will attempt login")
    except Exception as e:
        logger.exception("Failed to write IG session file from base64: %s", e)

# login (اگر قبلاً با session لاگین شده باشه ممکن نیازی به ورود دوباره نباشه)
try:
    cl.login(IG_USERNAME, IG_PASSWORD)
    logger.info("Instagram login OK")
    # در صورت نیاز میتونی سشن رو ذخیره کنی:
    try:
        cl.dump_settings(SESSION_FILE)
        logger.info("Saved IG session to %s", SESSION_FILE)
    except Exception:
        logger.info("dump_settings not available or failed; continuing")
except Exception as e:
    logger.exception("Instagram login failed: %s", e)
    # ادامه میده ولی هر درخواست اینستا احتمالا خطا میده — لاگ‌ها رو چک کن

# ---------- Telegram handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ربات دانلود پروفایل اینستاگرام هستم.\n"
        "کافیه یوزرنیم یا لینک اینستاگرام رو بفرستی."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    logger.info("Received message from %s: %s", update.effective_user.id, text)

    # استخراج یوزرنیم از لینک یا متن
    username = None
    m = re.search(r"instagram\.com/([A-Za-z0-9_.]+)", text)
    if m:
        username = m.group(1)
    elif re.match(r"^[A-Za-z0-9_.]+$", text):
        username = text

    if not username:
        await update.message.reply_text("❌ لطفاً یوزرنیم یا لینک اینستاگرام معتبر ارسال کنید.")
        return

    await update.message.reply_text("⏳ در حال دریافت پروفایل… لطفاً صبر کن.")

    try:
        user_id = cl.user_id_from_username(username)
        info = cl.user_info(user_id)

        profile_pic_url = str(getattr(info, "profile_pic_url_hd", None) or getattr(info, "profile_pic_url", None) or "")

        caption = (
            f"*👤 نام کاربری:* {escape_markdown(username, version=2)}\n"
            f"*📝 نام کامل:* {escape_markdown(info.full_name or '-', version=2)}\n"
            f"*👥 فالوورها:* {escape_markdown(f'{info.follower_count:,}', version=2)}\n"
            f"*👀 فالویینگ‌ها:* {escape_markdown(f'{info.following_count:,}', version=2)}\n"
            f"*🖼️ تعداد پست‌ها:* {escape_markdown(f'{info.media_count:,}', version=2)}\n"
            f"*🔒 خصوصی:* {escape_markdown('بله' if info.is_private else 'خیر', version=2)}\n"
            f"*✔️ تیک آبی:* {escape_markdown('بله' if info.is_verified else 'خیر', version=2)}\n\n"
            f"*ℹ️ بیوگرافی:*\n{escape_markdown(info.biography or '-', version=2)}"
        )

        if not profile_pic_url:
            await update.message.reply_text("⚠️ تصویر پروفایل پیدا نشد.")
            return

        await update.message.reply_photo(
            photo=profile_pic_url,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN_V2
        )

    except Exception as e:
        logger.exception("Error fetching profile for %s: %s", username, e)
        await update.message.reply_text(f"⚠️ خطا در گرفتن پروفایل: {e}")

# ---------- run bot (polling) ----------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    logger.info("Starting bot (polling)...")
    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()











# from instagrapi import Client
# from telegram import Update
# from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
# from telegram.helpers import escape_markdown
# from telegram.constants import ParseMode
# import re
# import logging

# # فعال کردن لاگ
# logging.basicConfig(level=logging.INFO)


# # تلگرام
# TOKEN = "7979842928:AAE0iRK0pDSbIMr18h8kmkQbbQm37lY3xzc"

# # اینستا
# cl = Client()
# cl.login("alialialimkg","ali@1384")


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(
#         "سلام! من ربات دانلود عکس پروفایل اینستاگرام هستم.\n"
#         "فقط کافیه یوزرنیم یا لینک پروفایل اینستا رو برام بفرستی."
#     )

# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_message = update.message.text.strip()
    
#     # پرینت پیام دریافتی در کنسول
#     print(f"[INFO] Received message: {user_message}")

#     # استخراج یوزرنیم از لینک یا متن
#     username = None
#     url_match = re.search(r"instagram\.com/([a-zA-Z0-9_.]+)", user_message)
#     if url_match:
#         username = url_match.group(1)
#     elif re.match(r"^[a-zA-Z0-9_.]+$", user_message):
#         username = user_message

#     if not username:
#         await update.message.reply_text("❌ لطفاً یک یوزرنیم یا لینک اینستاگرام معتبر ارسال کن.")
#         return

#     # ریپلای اولیه
#     await update.message.reply_text("⏳ لطفاً صبر کنید… در حال دریافت پروفایل")

#     try:
#         user_id = cl.user_id_from_username(username)
#         info = cl.user_info(user_id)

#         profile_pic_url = str(info.profile_pic_url_hd)

#         # آماده‌سازی اطلاعات پروفایل
#         full_name = info.full_name or "—"
#         biography = info.biography or "—"
#         followers = info.follower_count
#         followees = info.following_count
#         posts = info.media_count
#         is_private = "بله" if info.is_private else "خیر"
#         is_verified = "بله" if info.is_verified else "خیر"

#         # کپشن امن
#         caption = (
#             f"*👤 نام کاربری:* {escape_markdown(username, version=2)}\n"
#             f"*📝 نام کامل:* {escape_markdown(full_name, version=2)}\n"
#             f"*👥 فالوورها:* {escape_markdown(f'{followers:,}', version=2)}\n"
#             f"*👀 فالویینگ‌ها:* {escape_markdown(f'{followees:,}', version=2)}\n"
#             f"*🖼️ تعداد پست‌ها:* {escape_markdown(f'{posts:,}', version=2)}\n"
#             f"*🔒 خصوصی:* {escape_markdown(is_private, version=2)}\n"
#             f"*✔️ تیک آبی:* {escape_markdown(is_verified, version=2)}\n\n"
#             f"*ℹ️ بیوگرافی:*\n{escape_markdown(biography, version=2)}"
#         )

#         # ارسال عکس با کپشن کامل
#         await update.message.reply_photo(
#             photo=profile_pic_url,
#             caption=caption,
#             parse_mode=ParseMode.MARKDOWN_V2
#         )

#     except Exception as e:
#         await update.message.reply_text(f"⚠️ خطا: {e}")
#         logging.error(f"Error fetching profile for {username}: {e}")

# if __name__ == "__main__":
#     app = Application.builder().token(TOKEN).build()
#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
#     app.run_polling()
