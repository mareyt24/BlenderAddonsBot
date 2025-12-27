# file: bot.py
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config import BOT_TOKEN
from handlers import start, admin_command, handle_message, handle_callback

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Главная функция запуска бота"""
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    print("\n" + "=" * 50)
    print("🤖 Blender Addon Bot запущен!")
    print("=" * 50)
    print("👑 Админская панель доступна по команде /admin")
    print("🎬 Название видео автоматически получается с YouTube")
    print("📋 В списке видео показываются оригинальные названия")
    print("=" * 50 + "\n")

    app.run_polling()

if __name__ == '__main__':
    main()