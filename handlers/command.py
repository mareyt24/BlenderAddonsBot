# file: handlers/command.py
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from menus.main_menu import get_main_menu
from menus.admin_menu import get_admin_menu

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без username"

    print(f"\n🚀 СТАРТ БОТА")
    print(f"👤 Пользователь: {user_id} (@{username})")

    await update.message.reply_text(
        "🎬 **Blender Addon Bot**\n\nИспользуйте кнопки ниже:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /admin для администраторов"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без username"

    print(f"\n👑 ЗАПРОС АДМИН ПАНЕЛИ")
    print(f"👤 Пользователь: {user_id} (@{username})")

    # Проверяем, является ли пользователь админом
    if user_id not in ADMIN_IDS:
        print(f"❌ ОТКАЗАНО: Пользователь {user_id} не админ")
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return

    print(f"✅ ДОСТУП РАЗРЕШЕН: Админ {user_id}")
    await update.message.reply_text(
        "👑 **Панель администратора**\n\nВыберите действие:",
        reply_markup=get_admin_menu(),
        parse_mode="Markdown"
    )