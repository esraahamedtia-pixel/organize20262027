from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import logging

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# توكن البوت وبيانات Google
TOKEN = "8002759884:AAFXP2sHqoWk9qYF-dzInoU9Lftv8MyAbgY"
SHEET_ID = "1e7CiffvQHIExH3bTV4WZoKtVIHuF5IdTKZ_hoCFWv48"

FOLDER_IDS = {
    "📘 الأول الثانوي": "1VRBaTib6LWZMnPbFBcy-4LjhedMCDGEZ",
    "📗 الثاني الثانوي": "1ZkNFSh678ipZ0p3l5GjCeA-Otu6JDSA3",
    "📕 الثالث الثانوي": "1Mfb9Akrm4Ss1qoPax-bWVPYCC8lW0JQl",
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file("abuab2025-33317b8c00c0.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1


def get_drive_service():
    return build('drive', 'v3', credentials=creds)


# الحالات
ASK_NAME, ASK_PHONE = range(2)


# بدء المحادثة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 مرحبًا! من فضلك اكتب اسمك بالكامل.")
    return ASK_NAME


# حفظ الاسم
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("📞 من فضلك اكتب رقم تليفونك.")
    return ASK_PHONE


# حفظ البيانات ثم عرض السنوات
async def save_data_and_show_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    name = context.user_data.get('name', '')
    telegram_id = update.effective_user.id
    username = update.effective_user.username or ''
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    try:
        sheet.append_row([name, phone, str(telegram_id), username, now])
        keyboard = [["📘 الأول الثانوي", "📗 الثاني الثانوي", "📕 الثالث الثانوي"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("📚 اختر سنتك الدراسية:", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"خطأ في حفظ البيانات: {e}")
        await update.message.reply_text(f"❌ حصل خطأ أثناء حفظ البيانات: {e}")

    return ConversationHandler.END


# إلغاء المحادثة
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END


# عرض المواد كمجلدات (زر لكل مجلد)
async def handle_year_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    year = update.message.text
    folder_id = FOLDER_IDS.get(year)

    if not folder_id:
        await update.message.reply_text("❌ سنة دراسية غير معروفة.")
        return

    service = get_drive_service()
    query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])

    if not folders:
        await update.message.reply_text("❌ لا توجد مواد متاحة حالياً لهذه السنة.")
        return

    keyboard = [
        [InlineKeyboardButton(folder["name"], callback_data=f"browse_{folder['id']}")]
        for folder in folders
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📚 اختر المادة:", reply_markup=reply_markup)


# تصفح المجلدات ديناميكيًا: عرض فولدرات أو ملفات
async def browse_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    folder_id = query.data.replace("browse_", "")
    service = get_drive_service()
    query_str = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query_str, fields="files(id, name, mimeType)").execute()
    items = results.get('files', [])

    if not items:
        await query.edit_message_text("❌ لا توجد عناصر داخل هذا المجلد.")
        return

    folders = []
    files = []

    for item in items:
        if item["mimeType"] == "application/vnd.google-apps.folder":
            folders.append(item)
        else:
            files.append(item)

    if folders:
        keyboard = [
            [InlineKeyboardButton(folder["name"], callback_data=f"browse_{folder['id']}")]
            for folder in folders
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📁 اختر مجلدًا:", reply_markup=reply_markup)
        return

    # عرض الملفات فقط
    reply_text = "📄 الملفات:\n\n"
    for file in files:
        url = f"https://drive.google.com/file/d/{file['id']}/view"
        reply_text += f"🔹 [{file['name']}]({url})\n"

    await query.edit_message_text(reply_text, parse_mode='Markdown')


# تشغيل البوت
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_data_and_show_options)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_year_selection))
    app.add_handler(CallbackQueryHandler(browse_folder, pattern="^browse_"))

    print("✅ البوت شغال...")
    app.run_polling()


if __name__ == "__main__":
    main()
