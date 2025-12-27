# file: handlers/message.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# file: handlers/message.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from menus.main_menu import get_main_menu
from menus.addons_menu import get_categories_menu
from menus.notes_menu import get_notes_menu

logger = logging.getLogger(__name__)

# Импортируем базу данных
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import db
except ImportError:
    # Если не получается импортировать, создаем экземпляр напрямую
    from database import Database
    db = Database()
    
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    if update.message and update.message.text:
        text = update.message.text

        if text.lower() == "отмена":
            await handle_cancel(update, context)
            return

        main_menu_texts = [
            "📦 Выбрать аддон", "📝 Создать заметку", "🔍 Поиск заметок",
            "📒 Мои заметки", "ℹ️ Помощь", "Отмена"
        ]

        if text in main_menu_texts:
            await handle_main_menu(update, context)
        else:
            await handle_text_message(update, context)
    else:
        await handle_non_text_message(update, context)


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик главного меню"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "без username"
    text = update.message.text

    print(f"\n👤 ГЛАВНОЕ МЕНЮ: {user_id} выбрал '{text}'")

    if text == "📦 Выбрать аддон":
        await update.message.reply_text(
            "📂 **Выберите категорию:**",
            reply_markup=get_categories_menu(),
            parse_mode="Markdown"
        )

    elif text == "📝 Создать заметку":
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_note")]]
        await update.message.reply_text(
            "📝 **Введите название заметки:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        context.user_data['creating_note'] = True

    elif text == "🔍 Поиск заметок":
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_search")]]
        await update.message.reply_text(
            "🔍 **Введите запрос для поиска:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        context.user_data['searching_notes'] = True

    elif text == "📒 Мои заметки":
        user_id = update.effective_user.id
        notes = db.get_user_notes(user_id)

        if not notes:
            print(f"📭 Пользователь {user_id} просматривает пустые заметки")
            await update.message.reply_text(
                "📭 **У вас нет заметок.**",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            return

        print(f"📒 Пользователь {user_id} просматривает заметки ({len(notes)} шт.)")
        await update.message.reply_text(
            "📒 **Ваши заметки:**",
            reply_markup=get_notes_menu(notes),
            parse_mode="Markdown"
        )

    elif text == "ℹ️ Помощь":
        print(f"❓ Пользователь {user_id} запросил помощь")
        await update.message.reply_text(
            "📖 **Помощь:**\n\n"
            "🎬 **Blender Addon Bot** - бот для поиска аддонов Blender\n\n"
            "**Основные функции:**\n"
            "• 📦 Поиск аддонов по категориям\n"
            "• 📝 Создание заметок с хэштегами\n"
            "• 🔍 Поиск по заметкам\n"
            "• 🎬 Добавление полезных видео к аддонам\n"
            "• 👍👎 Оценка видео лайками/дизлайками\n\n"
            "**Для администраторов:** /admin\n\n"
            "**Отмена действий:** Используйте кнопку 'Отмена' под сообщением",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text

    print(f"\n📝 ПОЛУЧЕНО СООБЩЕНИЕ: {user_id} -> '{text}'")

    # ========== АДМИНСКИЕ ДЕЙСТВИЯ ==========
    if await handle_admin_text(update, context, text):
        return

    # ========== СОЗДАНИЕ ЗАМЕТКИ ==========
    if context.user_data.get('creating_note'):
        await handle_note_creation(update, context, text)

    # ========== ДОБАВЛЕНИЕ СОДЕРЖИМОГО ЗАМЕТКИ ==========
    elif context.user_data.get('adding_note_content'):
        await handle_note_content(update, context, text)

    # ========== ПОИСК ЗАМЕТОК ==========
    elif context.user_data.get('searching_notes'):
        await handle_note_search(update, context, text)

    # ========== ДОБАВЛЕНИЕ ВИДЕО ==========
    elif context.user_data.get('adding_video_url'):
        await handle_video_addition(update, context, text)


async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка админских текстовых сообщений"""
    from config import ADMIN_IDS
    from menus.admin_menu import get_admin_menu
    from data.addons_data import add_category, add_addon

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        return False

    # Добавление категории
    if context.user_data.get('admin_adding_category'):
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_admin")]]
        success = add_category(text)
        if success:
            await update.message.reply_text(
                f"✅ **Категория '{text}' добавлена!**",
                reply_markup=get_admin_menu(),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"⚠️ **Категория '{text}' уже существует.**",
                reply_markup=get_admin_menu(),
                parse_mode="Markdown"
            )
        context.user_data.pop('admin_adding_category', None)
        return True

    # Добавление аддона
    elif context.user_data.get('admin_adding_addon'):
        addon_data = context.user_data.get('admin_addon_data', {})
        step = addon_data.get('step', 0)

        if step == 0:  # Название
            addon_data['name'] = text
            addon_data['step'] = 1
            context.user_data['admin_addon_data'] = addon_data
            keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_admin")]]
            await update.message.reply_text(
                "📝 **Введите описание аддона:**",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

        elif step == 1:  # Описание аддона
            # УБИРАЕМ проверку на слово blender/блендер
            addon_data['description'] = text
            addon_data['step'] = 2
            context.user_data['admin_addon_data'] = addon_data

            keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_admin")]]
            await update.message.reply_text(
                "✅ **Описание принято!**\n\n"
                "🔗 **Теперь введите ссылку на GitHub (должна начинаться с https://github.com/):**",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

        elif step == 2:  # GitHub - добавляем проверку
            # Проверяем, что это ссылка на GitHub
            if not text.startswith("https://github.com/"):
                await update.message.reply_text(
                    "❌ **Ошибка:** Это не ссылка на GitHub.\n"
                    "Ссылка должна начинаться с https://github.com/\n\n"
                    "Пожалуйста, введите корректную ссылку на GitHub:",
                    parse_mode="Markdown"
                )
                # Остаемся на этом же шаге
                return

            addon_data['github'] = text
            addon_data['step'] = 3
            context.user_data['admin_addon_data'] = addon_data
            keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_admin")]]
            await update.message.reply_text(
                "🎬 **Введите ссылку на YouTube (должна быть youtube.com или youtu.be):**",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

        elif step == 3:  # YouTube - добавляем проверку
            # Проверяем, что это ссылка на YouTube
            if not ("youtube.com" in text or "youtu.be" in text):
                await update.message.reply_text(
                    "❌ **Ошибка:** Это не ссылка на YouTube.\n"
                    "Ссылка должна содержать youtube.com или youtu.be\n\n"
                    "Пожалуйста, введите корректную ссылку на YouTube:",
                    parse_mode="Markdown"
                )
                # Остаемся на этом же шаге
                return

            addon_data['youtube'] = text
            context.user_data['admin_addon_data'] = addon_data

            # Добавляем аддон
            success = add_addon(
                addon_data['category'],
                addon_data['name'],
                addon_data['description'],
                addon_data['github'],
                addon_data['youtube']
            )

            if success:
                await update.message.reply_text(
                    f"✅ **Аддон '{addon_data['name']}' добавлен в категорию '{addon_data['category']}'!**",
                    reply_markup=get_admin_menu(),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "❌ **Не удалось добавить аддон.**",
                    reply_markup=get_admin_menu(),
                    parse_mode="Markdown"
                )

            context.user_data.pop('admin_adding_addon', None)
            context.user_data.pop('admin_addon_data', None)
        return True

    return False

async def handle_note_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка создания заметки"""
    user_id = update.effective_user.id
    print(f"📝 {user_id}: создает заметку с названием '{text}'")

    context.user_data['note_title'] = text
    context.user_data.pop('creating_note', None)

    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_note")]]
    await update.message.reply_text(
        f"📝 **Название:** {text}\n\n"
        f"Теперь отправьте содержимое заметки (текст, фото, видео, документ).\n"
        f"Я сохраню только ссылку на это сообщение.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    context.user_data['adding_note_content'] = True


async def handle_note_content(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка содержимого заметки"""
    user_id = update.effective_user.id
    title = context.user_data.get('note_title', 'Без названия')

    print(f"📝 {user_id}: сохраняет заметку '{title}'")

    message_id = update.message.message_id
    chat_id = update.message.chat_id

    note_id, hashtag = db.save_note(user_id, title, message_id, chat_id)

    print(f"✅ Заметка сохранена: ID={note_id}, хэштег={hashtag}")

    await update.message.reply_text(
        f"✅ **Заметка сохранена!**\n\n"
        f"🏷️ **Хэштег:** #{hashtag}\n"
        f"📝 **Название:** {title}\n\n"
        f"**Как быстро найти заметку позже:**\n"
        f"1. Используйте поиск по хэштегу '#{hashtag}'\n"
        f"2. Или найдите в истории чата сообщение с этим хэштегом",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

    context.user_data.pop('adding_note_content', None)
    context.user_data.pop('note_title', None)


async def handle_note_search(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка поиска заметок"""
    user_id = update.effective_user.id

    print(f"\n🔍 ПОИСК ЗАМЕТОК")
    print(f"👤 Пользователь: {user_id}")
    print(f"🔍 Запрос: '{text}'")

    notes = db.search_notes(user_id, text)

    if not notes:
        print(f"🔍 НИЧЕГО НЕ НАЙДЕНО")
        await update.message.reply_text(
            f"🔍 **По запросу '{text}' ничего не найдено.**",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    else:
        print(f"🔍 НАЙДЕНО {len(notes)} ЗАМЕТОК")
        await update.message.reply_text(
            f"🔍 **Найдено заметок:** {len(notes)}",
            reply_markup=get_notes_menu(notes),
            parse_mode="Markdown"
        )

    context.user_data.pop('searching_notes', None)


async def handle_video_addition(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка добавления видео с проверкой релевантности"""
    user_id = update.effective_user.id

    print(f"\n🎬 ДОБАВЛЕНИЕ ВИДЕО")
    print(f"👤 Пользователь: {user_id}")
    print(f"🔗 Ссылка: {text}")

    # Проверяем, является ли сообщение ссылкой
    if not ("youtube.com" in text or "youtu.be" in text):
        await update.message.reply_text(
            "❌ **Это не YouTube ссылка.**\n\n"
            "Пожалуйста, отправьте корректную ссылку на YouTube видео.\n"
            "Пример: https://www.youtube.com/watch?v=...",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        context.user_data.pop('adding_video_url', None)
        context.user_data.pop('add_video', None)
        return

    # Показываем сообщение о загрузке
    loading_msg = await update.message.reply_text(
        "⏳ **Проверяю видео...**\n\n"
        "Это может занять несколько секунд.",
        parse_mode="Markdown"
    )

    try:
        # Получаем информацию о видео через новую функцию
        from utils.youtube import get_video_info
        success, result = await get_video_info(text)

        if not success:
            print(f"❌ Ошибка при получении информации: {result}")
            # result уже содержит полное отформатированное сообщение об ошибке
            await loading_msg.edit_text(
                result,  # <-- Просто передаём готовое сообщение
                parse_mode="Markdown"  # <-- Убедитесь, что оно в Markdown
            )

            # Очищаем временные данные
            context.user_data.pop('adding_video_url', None)
            context.user_data.pop('add_video', None)

            # Предлагаем попробовать снова
            await update.message.reply_text(
                "❌ **Видео не добавлено.**\n\n"
                "Вы можете попробовать другую ссылку.",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            return

        # Если success == True, то result - это просто строка с названием видео
        title = result  # <-- ТЕПЕРЬ ПРОСТО СТРОКА!
        # Проверка на Blender уже пройдена внутри get_video_info
        print(f"✅ Видео прошло проверку: '{title}'")

        # Обновляем сообщение о загрузке
        await loading_msg.edit_text(
            f"✅ **Видео проверено!**\n\n"
            f"🎬 **{title}**\n\n"
            f"Добавляю в базу данных...",
            parse_mode="Markdown"
        )

    except Exception as e:
        print(f"❌ Ошибка при проверке видео: {e}")
        await loading_msg.edit_text(
            f"❌ **Произошла ошибка при проверке видео.**\n\n"
            f"Пожалуйста, попробуйте позже или используйте другую ссылку.",
            parse_mode="Markdown"
        )

        # Очищаем временные данные
        context.user_data.pop('adding_video_url', None)
        context.user_data.pop('add_video', None)

        # Предлагаем вернуться в меню
        await update.message.reply_text(
            "❌ **Видео не добавлено.**\n\n"
            "Вы можете попробовать добавить другое видео.",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        return

    # Добавляем видео в базу данных
    video_data = context.user_data.get('add_video', {})

    if not video_data:
        print(f"❌ ОШИБКА ДАННЫХ: нет данных аддона")
        await update.message.reply_text(
            "❌ **Ошибка данных.**\n\n"
            "Начните добавление видео заново.",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        return

    # Получаем аддон
    from data.addons_data import get_addon
    addon = get_addon(video_data['category'], video_data['index'])

    if not addon:
        print(f"❌ АДДОН НЕ НАЙДЕН")
        await update.message.reply_text(
            "❌ **Аддон не найден.**",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        return

    # Добавляем видео в базу
    from database import db
    success, result = db.add_video(
        video_data['category'],
        video_data['index'],
        user_id,
        text,  # URL видео
        title  # Название с YouTube
    )

    if success:
        video_id = result
        print(f"✅ ВИДЕО ДОБАВЛЕНО: ID {video_id}, название: '{title}'")

        # Логируем действие
        db.log_video_action(video_id, user_id, "add")

        # Удаляем сообщение о загрузке
        try:
            await loading_msg.delete()
        except:
            pass

        # Отправляем подтверждение
        await update.message.reply_text(
            f"✅ **Видео успешно добавлено!**\n\n"
            f"🎬 **Название:** {title}\n"
            f"🔗 **Ссылка:** {text}\n"
            f"📦 **Аддон:** {addon['name']}\n"
            f"👤 **Добавил:** @{update.effective_user.username if update.effective_user.username else 'пользователь'}\n\n"
            f"**Что дальше:**\n"
            f"• Другие пользователи смогут оценить видео лайками/дизлайками\n"
            f"• Видео появится в списке полезных видео для этого аддона\n"
            f"• Вы можете удалить свое видео в любое время",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )

        # Также показываем кнопки для просмотра видео
        keyboard = [
            [
                InlineKeyboardButton("📺 Посмотреть видео", url=text),
                InlineKeyboardButton("📋 К списку видео",
                                     callback_data=f"videos:{video_data['category']}:{video_data['index']}")
            ]
        ]
        await update.message.reply_text(
            "🔗 **Быстрые ссылки:**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:
        print(f"❌ ОШИБКА ПРИ СОХРАНЕНИИ: {result}")

        # Удаляем сообщение о загрузке
        try:
            await loading_msg.delete()
        except:
            pass

        await update.message.reply_text(
            f"❌ **Не удалось добавить видео.**\n\n"
            f"**Ошибка:** {result}\n\n"
            f"Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )

    # Очищаем временные данные
    context.user_data.pop('adding_video_url', None)
    context.user_data.pop('add_video', None)


async def handle_non_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка не текстовых сообщений"""
    if context.user_data.get('adding_note_content'):
        user_id = update.effective_user.id
        title = context.user_data.get('note_title', 'Без названия')

        print(f"📝 {user_id}: сохраняет заметку '{title}' (не текстовое содержимое)")

        message_id = update.message.message_id
        chat_id = update.message.chat_id

        note_id, hashtag = db.save_note(user_id, title, message_id, chat_id)

        print(f"✅ Заметка сохранена: ID={note_id}, хэштег={hashtag}")

        await update.message.reply_text(
            f"✅ **Заметка сохранена!**\n\n"
            f"🏷️ **Хэштег:** #{hashtag}\n"
            f"📝 **Название:** {title}\n\n"
            f"**Как быстро найти заметку позже:**\n"
            f"1. Используйте поиск по хэштегу '#{hashtag}'\n"
            f"2. Или найдите в истории чата сообщение с этим хэштегом",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )

        context.user_data.pop('adding_note_content', None)
        context.user_data.pop('note_title', None)


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка отмены действий"""
    user_id = update.effective_user.id
    print(f"❌ Пользователь {user_id} отменил действие")

    context.user_data.clear()
    await update.message.reply_text(
        "❌ **Отменено.** Возвращаемся в главное меню.",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )