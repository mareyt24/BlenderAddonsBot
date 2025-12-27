from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_notes_menu(notes):
    """Список заметок - inline кнопки"""
    keyboard = []
    for note in notes:
        note_id, title, hashtag, views, created_at = note
        short_title = title[:20] + "..." if len(title) > 20 else title
        button_text = f"📄 {short_title}"
        if views and views > 0:
            button_text += f" (👁️{views})"

        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"note:{note_id}"
        )])

    # Убрали только "🏠 Главное меню", но не добавляем других кнопок
    return InlineKeyboardMarkup(keyboard)