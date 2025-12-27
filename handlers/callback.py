# file: handlers/callback.py
import logging
import html
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from menus.main_menu import get_main_menu
from menus.addons_menu import (
    get_categories_menu, get_addons_menu, get_addon_details_menu,
    get_videos_list_menu, get_video_view_menu, get_add_video_menu
)
from menus.notes_menu import get_notes_menu
from menus.admin_menu import get_admin_menu, get_addon_management_menu
from data.addons_data import get_categories, get_addons, get_addon, delete_addon
from utils.youtube import extract_video_id, get_youtube_title
logger = logging.getLogger(__name__)

# Импортируем базу данных
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import db
except ImportError:
    from database import Database

    db = Database()


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline кнопок"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    print(f"\n🖱️ КНОПКА: {user_id} нажал '{data}'")

    # Обработка отмен
    if data.startswith("cancel_"):
        await handle_cancel_actions(query, context, data)
        return

    # Главное меню
    if data == "main":
        await handle_main_menu(query, context)

    # Админское меню
    elif data == "admin":
        await handle_admin_menu(query, user_id)

    # Админские действия
    elif data.startswith("admin_"):
        await handle_admin_actions(query, context, data, user_id)

    # ВСТАВЬТЕ ЗДЕСЬ НОВЫЕ ОБРАБОТЧИКИ:
    # Статистика по аддонам
    elif data.startswith("admin_stats_cat:"):
        await handle_admin_addon_stats_category(query, data)

    elif data.startswith("admin_stats_addon:"):
        await handle_admin_addon_stats_view(query, data)


    # Категории
    elif data == "cats":
        await query.edit_message_text(
            "📂 **Выберите категорию:**",
            reply_markup=get_categories_menu(),
            parse_mode="Markdown"
        )


    # Выбор категории
    elif data.startswith("cat:"):
        await handle_category_selection(query, data)

    # Выбор аддона
    elif data.startswith("add:"):
        await handle_addon_selection(query, data)

    # Список видео для аддона
    elif data.startswith("videos:"):
        await handle_videos_list(query, data)

    # Просмотр видео
    elif data.startswith("view_video:"):
        await handle_video_view(query, data)

    # Добавление видео (начало)
    elif data.startswith("add_video:"):
        await handle_video_addition_start(query, context, data)

    # Лайк видео
    elif data.startswith("like_video:"):
        await handle_video_like(query, data, user_id)

    # Дизлайк видео
    elif data.startswith("dislike_video:"):
        await handle_video_dislike(query, data, user_id)

    # Просмотр заметки
    elif data.startswith("note:"):
        await handle_note_view(query, data, context)

    # Возврат к списку заметок
    elif data == "notes":
        await handle_notes_list(query, user_id)

    # Обработка GitHub и YouTube ссылок
    elif data.startswith("github:") or data.startswith("youtube:"):
        await handle_link_click(query, data, context)


async def handle_cancel_actions(query, context, data):
    """Обработка отмен действий"""
    if data == "cancel_note":
        context.user_data.clear()
        await query.edit_message_text(
            "❌ **Добавление заметки отменено.**",
            parse_mode="Markdown"
        )

    elif data == "cancel_search":
        context.user_data.clear()
        await query.edit_message_text(
            "❌ **Поиск отменен.**",
            parse_mode="Markdown"
        )

    elif data == "cancel_admin":
        await query.edit_message_text(
            "❌ **Действие отменено.**",
            reply_markup=get_admin_menu(),
            parse_mode="Markdown"
        )

    elif data.startswith("cancel_add_video:"):
        parts = data.split(":")
        if len(parts) >= 3:
            category = parts[1]
            index = int(parts[2])
            addon = get_addon(category, index)

            if addon:
                context.user_data.clear()
                await query.edit_message_text(
                    f"❌ **Добавление видео отменено.**\n\n"
                    f"🎯 **{addon['name']}**\n\n"
                    f"📝 {addon['description']}\n\n"
                    f"**Официальные ссылки:**",
                    reply_markup=get_addon_details_menu(category, index),
                    parse_mode="Markdown"
                )


async def handle_main_menu(query, context):
    """Обработка возврата в главное меню"""
    context.user_data.clear()
    await query.edit_message_text(
        "🏠 **Вы вернулись в главное меню.**\n\n"
        "Используйте кнопки внизу экрана для навигации.",
        parse_mode="Markdown"
    )


async def handle_admin_menu(query, user_id):
    """Обработка админского меню"""
    if user_id not in ADMIN_IDS:
        await query.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    await query.edit_message_text(
        "👑 **Панель администратора**\n\nВыберите действие:",
        reply_markup=get_admin_menu(),
        parse_mode="Markdown"
    )


async def handle_admin_actions(query, context, data, user_id):
    """Обработка админских действий"""
    if user_id not in ADMIN_IDS:
        await query.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    if data == "admin_addons":
        await query.edit_message_text(
            "📦 **Управление аддонами**\n\nВыберите действие:",
            reply_markup=get_addon_management_menu(),
            parse_mode="Markdown"
        )

    elif data == "admin_stats":
        await handle_admin_stats(query, user_id)

    elif data == "admin_add_category":
        await handle_admin_add_category(query, context)

    elif data == "admin_add_addon":
        await handle_admin_add_addon_start(query)

    elif data.startswith("admin_addon_cat:"):
        await handle_admin_add_addon_category(query, context, data)

    elif data == "admin_edit_addon":
        await handle_admin_edit_addon(query)

    elif data == "admin_delete_addon":
        await handle_admin_delete_addon_start(query)

    elif data.startswith("admin_delete_addon_confirm:"):
        await handle_admin_delete_addon_confirm(query, data)

    elif data.startswith("admin_do_delete:"):
        await handle_admin_do_delete(query, data)

    elif data == "admin_addon_stats":
        await handle_admin_addon_stats_start(query)

    # ДОБАВЬТЕ ЭТИ ДВА УСЛОВИЯ:
    elif data.startswith("admin_stats_cat:"):
        await handle_admin_addon_stats_category(query, data)

    elif data.startswith("admin_stats_addon:"):
        await handle_admin_addon_stats_view(query, data)


async def handle_admin_stats(query, user_id):
    """Обработка статистики админа"""
    from data.addons_data import get_addon

    stats = db.get_overall_stats()

    print(f"👑 АДМИН {user_id} запросил статистику")

    message = "📊 **Статистика бота**\n\n"

    # Общая статистика
    message += "📈 **Общая статистика:**\n"
    message += f"• Заметок: {stats.get('notes', {}).get('total', 0)}\n"
    message += f"• Просмотров заметок: {stats.get('notes', {}).get('total_views', 0)}\n"
    message += f"• Видео: {stats.get('videos', {}).get('total', 0)}\n"
    message += f"• Просмотров видео: {stats.get('videos', {}).get('total_views', 0)}\n"
    message += f"• Лайков видео: {stats.get('videos', {}).get('total_likes', 0)}\n"
    message += f"• Дизлайков видео: {stats.get('videos', {}).get('total_dislikes', 0)}\n"
    message += f"• Просмотров аддонов: {stats.get('addons', {}).get('total_views', 0)}\n\n"  # НОВОЕ

    # Статистика пользователей
    message += "👥 **Пользователи:**\n"
    message += f"• Создавали заметки: {stats.get('users', {}).get('notes', 0)}\n"
    message += f"• Добавляли видео: {stats.get('users', {}).get('videos', 0)}\n"
    message += f"• Оценивали видео: {stats.get('users', {}).get('likes', 0)}\n\n"

    # Топ аддонов по просмотрам (НОВОЕ)
    top_addons = db.get_top_addons_by_views(limit=5, days=30)
    if top_addons:
        message += "🏆 **Топ-5 аддонов по просмотрам (30 дней):**\n"
        for i, addon_data in enumerate(top_addons, 1):
            category, addon_index, views, created_at = addon_data
            try:
                addon = get_addon(category, addon_index)
                addon_name = addon['name'] if addon else "Неизвестный аддон"
                message += f"{i}. {addon_name}\n"
                message += f"   📦 Категория: {category}\n"
                message += f"   👁️ Просмотров: {views}\n"
            except:
                message += f"{i}. Ошибка данных\n"
                continue
        message += "\n"

    # Топ видео
    top_videos = db.get_top_videos(limit=5, days=7)
    if top_videos:
        message += "🎬 **Топ-5 видео (7 дней):**\n"
        for i, video in enumerate(top_videos, 1):
            try:
                video_id, title, url, views, likes, dislikes, category, index = video
                short_title = title[:20] + "..." if len(title) > 20 else title

                try:
                    addon = get_addon(category, index)
                    addon_name = addon['name'] if addon else "Неизвестный аддон"
                except:
                    addon_name = "Неизвестный аддон"

                message += f"{i}. {short_title}\n"
                message += f"   📦 Аддон: {addon_name}\n"
                message += f"   👁️ Просмотров: {views}\n"
                message += f"   👍 {likes} | 👎 {dislikes}\n"
            except ValueError as e:
                print(f"⚠️ Ошибка распаковки данных видео: {e}")
                message += f"{i}. Ошибка данных\n"
                continue

    await query.edit_message_text(
        message,
        parse_mode="Markdown"
    )


async def handle_admin_add_category(query, context):
    """Начало добавления категории"""
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_admin")]]
    await query.edit_message_text(
        "➕ **Добавление категории**\n\n"
        "Введите название новой категории в чат:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    context.user_data['admin_adding_category'] = True


async def handle_admin_add_addon_start(query):
    """Начало добавления аддона"""
    categories = get_categories()
    if not categories:
        await query.edit_message_text(
            "❌ **Сначала добавьте категорию!**",
            reply_markup=get_addon_management_menu(),
            parse_mode="Markdown"
        )
        return

    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(category, callback_data=f"admin_addon_cat:{category}")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_admin")])

    await query.edit_message_text(
        "➕ **Добавление аддона**\n\n"
        "Сначала выберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_admin_add_addon_category(query, context, data):
    """Выбор категории для добавления аддона"""
    category = data.split(":")[1]

    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_admin")]]
    await query.edit_message_text(
        f"➕ **Добавление аддона в категорию '{category}'**\n\n"
        "Введите название аддона в чат:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    context.user_data['admin_adding_addon'] = True
    context.user_data['admin_addon_data'] = {
        'category': category,
        'step': 0
    }


async def handle_admin_edit_addon(query):
    """Редактирование аддона"""
    await query.edit_message_text(
        "✏️ **Редактирование аддона**\n\n"
        "⚠️ **Редактирование временно недоступно**\n"
        "Используйте удаление и добавление нового аддона.",
        reply_markup=get_addon_management_menu(),
        parse_mode="Markdown"
    )


async def handle_admin_delete_addon_start(query):
    """Начало удаления аддона"""
    categories = get_categories()
    if not categories:
        await query.edit_message_text(
            "❌ **Нет категорий для удаления!**",
            reply_markup=get_addon_management_menu(),
            parse_mode="Markdown"
        )
        return

    keyboard = []
    for category in categories:
        addons = get_addons(category)
        if addons:
            for i, addon in enumerate(addons):
                keyboard.append([InlineKeyboardButton(
                    f"{category}: {addon['name']}",
                    callback_data=f"admin_delete_addon_confirm:{category}:{i}"
                )])

    if not keyboard:
        await query.edit_message_text(
            "❌ **Нет аддонов для удаления!**",
            reply_markup=get_addon_management_menu(),
            parse_mode="Markdown"
        )
        return

    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="admin_addons")])

    await query.edit_message_text(
        "🗑️ **Удаление аддона**\n\n"
        "Выберите аддон для удаления:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_admin_delete_addon_confirm(query, data):
    """Подтверждение удаления аддона"""
    parts = data.split(":")
    if len(parts) >= 3:
        category = parts[1]
        index = int(parts[2])

        addon = get_addon(category, index)
        if not addon:
            await query.edit_message_text(
                "❌ **Аддон не найден!**",
                reply_markup=get_addon_management_menu(),
                parse_mode="Markdown"
            )
            return

        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить",
                                     callback_data=f"admin_do_delete:{category}:{index}"),
                InlineKeyboardButton("❌ Нет, отменить",
                                     callback_data="admin_addons")
            ]
        ]

        await query.edit_message_text(
            f"🗑️ **Удаление аддона**\n\n"
            f"Вы уверены, что хотите удалить аддон:\n"
            f"**{addon['name']}** из категории {category}?\n\n"
            f"⚠️ **Это действие необратимо!**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def handle_admin_do_delete(query, data):
    """Удаление аддона"""
    parts = data.split(":")
    if len(parts) >= 3:
        category = parts[1]
        index = int(parts[2])

        success = delete_addon(category, index)
        if success:
            await query.edit_message_text(
                f"✅ **Аддон удален из категории '{category}'!**",
                reply_markup=get_addon_management_menu(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"❌ **Не удалось удалить аддон!**",
                reply_markup=get_addon_management_menu(),
                parse_mode="Markdown"
            )


async def handle_admin_addon_stats_start(query):
    """Начало просмотра статистики по аддонам"""
    categories = get_categories()
    if not categories:
        await query.edit_message_text(
            "❌ **Нет категорий!**",
            reply_markup=get_addon_management_menu(),
            parse_mode="Markdown"
        )
        return

    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(category, callback_data=f"admin_stats_cat:{category}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_addons")])

    await query.edit_message_text(
        "📊 **Статистика по аддонам**\n\n"
        "Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_admin_addon_stats_category(query, data):
    """Выбор категории для статистики по аддону"""
    category = data.split(":")[1]
    addons = get_addons(category)

    if not addons:
        await query.edit_message_text(
            f"❌ **В категории '{category}' нет аддонов!**",
            reply_markup=get_addon_management_menu(),
            parse_mode="Markdown"
        )
        return

    keyboard = []
    for i, addon in enumerate(addons):
        keyboard.append([InlineKeyboardButton(addon['name'], callback_data=f"admin_stats_addon:{category}:{i}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_addon_stats")])

    await query.edit_message_text(
        f"📊 **Статистика по аддонам**\n\n"
        f"Категория: {category}\n"
        f"Выберите аддон:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_admin_addon_stats_view(query, data):
    """Просмотр статистики по аддону"""
    parts = data.split(":")
    if len(parts) >= 3:
        category = parts[1]
        index = int(parts[2])

        addon = get_addon(category, index)
        if not addon:
            await query.edit_message_text(
                "❌ **Аддон не найден!**",
                reply_markup=get_addon_management_menu(),
                parse_mode="Markdown"
            )
            return

        videos = db.get_videos(category, index, limit=1000)

        total_videos = len(videos)
        total_views = sum(video[7] for video in videos) if total_videos > 0 else 0
        total_likes = sum(video[5] for video in videos) if total_videos > 0 else 0
        total_dislikes = sum(video[6] for video in videos) if total_videos > 0 else 0

        # ПОЛУЧАЕМ КОЛИЧЕСТВО ПРОСМОТРОВ АДДОНА (НОВОЕ)
        addon_views = db.get_addon_views(category, index)

        top_videos = db.get_top_videos(category, index, limit=5, days=30)

        message = f"📊 **Статистика аддона:** {addon['name']}\n\n"
        message += f"📦 **Категория:** {category}\n\n"

        # Статистика просмотров аддона (НОВОЕ)
        message += f"📈 **Просмотры карточки аддона:** {addon_views}\n\n"

        # Статистика по видео
        message += f"🎬 **Статистика по видео:**\n"
        message += f"• Всего видео: {total_videos}\n"
        message += f"• Всего просмотров видео: {total_views}\n"
        message += f"• Всего лайков: {total_likes}\n"
        message += f"• Всего дизлайков: {total_dislikes}\n\n"

        message += f"🔗 **Ссылки аддона:**\n"
        if addon.get('github'):
            message += f"• GitHub: {addon['github']}\n"
        if addon.get('youtube'):
            message += f"• YouTube: {addon['youtube']}\n"

        # Топ видео
        if top_videos:
            message += "\n🏆 **Топ видео за 30 дней:**\n"
            for i, video in enumerate(top_videos, 1):
                try:
                    video_id, title, url, views, likes, dislikes, cat, idx = video
                    short_title = title[:20] + "..." if len(title) > 20 else title
                    message += f"{i}. {short_title}\n"
                    message += f"   👁️ {views} | 👍 {likes} | 👎 {dislikes}\n"
                except ValueError as e:
                    print(f"⚠️ Ошибка распаковки данных топа видео: {e}")
                    message += f"{i}. Ошибка данных\n"
                    continue

        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data=f"admin_stats_cat:{category}")]
        ]

        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def handle_category_selection(query, data):
    """Обработка выбора категории"""
    category = data[4:]
    print(f"📂 {query.from_user.id} выбрал категорию '{category}'")
    await query.edit_message_text(
        f"📦 **Аддоны в категории '{category}'**\n\n**Выберите аддон:**",
        reply_markup=get_addons_menu(category),
        parse_mode="Markdown"
    )


async def handle_addon_selection(query, data):
    """Обработка выбора аддона"""
    parts = data.split(":")
    if len(parts) >= 3:
        category = parts[1]
        index = int(parts[2])
        print(f"📦 {query.from_user.id} выбрал аддон {category}/{index}")

        # ЛОГИРУЕМ ПРОСМОТР АДДОНА (НОВОЕ)
        db.increment_addon_views(category, index)

        addon = get_addon(category, index)

        if addon:
            videos = db.get_videos(category, index)

            await query.edit_message_text(
                f"🎯 **{addon['name']}**\n\n"
                f"📝 {addon['description']}\n\n"
                f"**Официальные ссылки:**",
                reply_markup=get_addon_details_menu(
                    category, index,
                    has_videos=len(videos) > 0
                ),
                parse_mode="Markdown"
            )


async def handle_videos_list(query, data):
    """Обработка списка видео"""
    parts = data.split(":")
    if len(parts) >= 3:
        category = parts[1]
        index = int(parts[2])
        print(f"🎬 {query.from_user.id} просматривает видео для аддона {category}/{index}")
        videos = db.get_videos(category, index)
        addon = get_addon(category, index)

        if videos and len(videos) > 0:
            await query.edit_message_text(
                f"🎬 **Полезные видео для {addon['name']}**\n\n"
                f"Выберите видео для просмотра (показаны оригинальные названия с YouTube):",
                reply_markup=get_videos_list_menu(videos, category, index),
                parse_mode="Markdown"
            )
        else:
            print(f"🎬 Нет видео для аддона {category}/{index}")
            await query.edit_message_text(
                f"🎬 **Полезные видео для {addon['name']}**\n\n"
                f"Пока нет видео для этого аддона.\n\n"
                f"Будьте первым, кто добавит полезное видео!",
                reply_markup=get_add_video_menu(category, index),
                parse_mode="Markdown"
            )


async def handle_video_view(query, data):
    """Обработка просмотра видео"""
    video_id = int(data.split(":")[1])
    video = db.get_video_by_id(video_id)

    if video:
        # Логируем просмотр
        db.log_video_action(video_id, query.from_user.id, "view")

        v_id, category, index, user_id_video, youtube_url, title, description, likes, dislikes, views, verified, created_at = video
        addon = get_addon(category, index)

        safe_title = html.escape(title)
        safe_description = html.escape(description) if description else "Нет описания"

        message_text = f"🎬 <b>{safe_title}</b>\n\n"
        message_text += f"🔗 <a href='{youtube_url}'>{youtube_url}</a>\n\n"
        message_text += f"📝 {safe_description}\n\n"
        message_text += f"👁️ {views} просмотров | 👍 {likes} | 👎 {dislikes}\n\n"
        message_text += f"Для аддона: <b>{addon['name']}</b>"

        await query.edit_message_text(
            message_text,
            reply_markup=get_video_view_menu(v_id, category, index),
            parse_mode="HTML",
            disable_web_page_preview=False
        )


async def handle_video_addition_start(query, context, data):
    """Начало добавления видео"""
    parts = data.split(":")
    if len(parts) >= 3:
        category = parts[1]
        index = int(parts[2])
        print(f"🎬 {query.from_user.id} начал добавление видео для аддона {category}/{index}")

        context.user_data['add_video'] = {
            'category': category,
            'index': index
        }

        await query.edit_message_text(
            "🎬 **Добавление полезного видео**\n\n"
            "Отправьте ссылку на YouTube видео в чат:\n\n"
            "Пример: https://www.youtube.com/watch?v=...\n\n"
            "Я автоматически получу название видео с YouTube.",
            reply_markup=get_add_video_menu(category, index),
            parse_mode="Markdown"
        )

        context.user_data['adding_video_url'] = True


async def handle_video_like(query, data, user_id):
    """Обработка лайка видео"""
    video_id = int(data.split(":")[1])
    # Логируем лайк
    db.log_video_action(video_id, user_id, "like")
    success, message = db.rate_video(video_id, user_id, is_like=True)
    await query.answer(message, show_alert=True)

    if success:
        await update_video_view(query, video_id)


async def handle_video_dislike(query, data, user_id):
    """Обработка дизлайка видео"""
    video_id = int(data.split(":")[1])
    # Логируем дизлайк
    db.log_video_action(video_id, user_id, "dislike")
    success, message = db.rate_video(video_id, user_id, is_like=False)
    await query.answer(message, show_alert=True)

    if success:
        await update_video_view(query, video_id)


async def update_video_view(query, video_id):
    """Обновление просмотра видео после оценки"""
    video = db.get_video_by_id(video_id)
    if video:
        v_id, category, index, user_id_video, youtube_url, title, description, likes, dislikes, views, verified, created_at = video
        addon = get_addon(category, index)

        safe_title = html.escape(title)
        safe_description = html.escape(description) if description else "Нет описания"

        message_text = f"🎬 <b>{safe_title}</b>\n\n"
        message_text += f"🔗 <a href='{youtube_url}'>{youtube_url}</a>\n\n"
        message_text += f"📝 {safe_description}\n\n"
        message_text += f"👁️ {views} просмотров | 👍 {likes} | 👎 {dislikes}\n\n"
        message_text += f"Для аддона: <b>{addon['name']}</b>"

        await query.edit_message_text(
            message_text,
            reply_markup=get_video_view_menu(v_id, category, index),
            parse_mode="HTML",
            disable_web_page_preview=False
        )


async def handle_note_view(query, data, context):
    """Обработка просмотра заметки"""
    note_id = int(data[5:])
    note = db.get_note(note_id)

    if note:
        message_id = note[4]
        chat_id = note[5]
        title = note[2]
        hashtag = note[3]
        user_id_note = note[1]
        views = note[6] if len(note) > 6 else 0

        print(f"📄 {query.from_user.id} открывает заметку {note_id}: '{title}'")

        # Увеличиваем счетчик просмотров
        db.increment_note_views(note_id)

        try:
            # Отправляем сообщение-указатель, которое будет ссылаться на оригинальную заметку
            # Это заставит Telegram прокрутить ленту до нужного сообщения
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"📄 **Заметка: {title}**\n\n"
                     f"Нажмите на это сообщение, чтобы Telegram прокрутил ленту к заметке.\n"
                     f"Хэштег: #{hashtag}",
                reply_to_message_id=message_id,
                parse_mode="Markdown"
            )

            # Редактируем сообщение с кнопками
            await query.edit_message_text(
                f"✅ **Сообщение-указатель отправлено!**\n\n"
                f"Telegram должен прокрутить ленту к заметке:\n"
                f"📄 **{title}**\n"
                f"🏷️ #{hashtag}\n"
                f"👁️ Просмотров: {views + 1}",
                parse_mode="Markdown"
            )

        except Exception as e:
            print(f"❌ Ошибка при создании reply-сообщения: {e}")

            # Если не удалось отправить reply, показываем информацию обычным способом
            await query.edit_message_text(
                f"📄 **{title}**\n\n"
                f"🏷️ **Хэштег:** #{hashtag}\n"
                f"👤 **Автор:** {user_id_note}\n"
                f"👁️ **Просмотров:** {views + 1}\n\n"
                f"**Как найти заметку:**\n"
                f"1. Вернитесь в наш личный чат\n"
                f"2. Найдите сообщение с хэштегом: #{hashtag}\n"
                f"3. Используйте поиск по хэштегу в чате",
                parse_mode="Markdown"
            )


async def handle_notes_list(query, user_id):
    """Обработка списка заметок"""
    notes = db.get_user_notes(user_id)

    if not notes:
        await query.edit_message_text(
            "📭 **У вас нет заметок.**",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "📒 **Ваши заметки:**",
            reply_markup=get_notes_menu(notes),
            parse_mode="Markdown"
        )


async def handle_link_click(query, data, context):
    """Обработка кликов по ссылкам GitHub и YouTube"""
    parts = data.split(":")
    link_type = parts[0]

    if link_type == "github":
        category = parts[1]
        index = int(parts[2])
        addon = get_addon(category, index)
        if addon and addon.get("github"):
            # Логируем клик
            db.log_link_click(query.from_user.id, "github", addon["github"], category, index)
            await query.answer(f"Открываю GitHub... (Кликов: {db.get_addon_link_stats(category, index, 30).get('github', {}).get('recent_clicks', 0) + 1})", show_alert=False)
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"🔗 **GitHub ссылка для {addon['name']}:**\n{addon['github']}"
            )

    elif link_type == "youtube":
        category = parts[1]
        index = int(parts[2])
        addon = get_addon(category, index)
        if addon and addon.get("youtube"):
            db.log_link_click(query.from_user.id, "youtube", addon["youtube"], category, index)
            await query.answer(f"Открываю YouTube... (Кликов: {db.get_addon_link_stats(category, index, 30).get('youtube', {}).get('recent_clicks', 0) + 1})", show_alert=False)
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"🎬 **YouTube ссылка для {addon['name']}:**\n{addon['youtube']}"
            )