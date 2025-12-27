from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    """Главное меню - reply кнопки внизу"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("📦 Выбрать аддон")],
        [KeyboardButton("📝 Создать заметку"), KeyboardButton("🔍 Поиск заметок")],
        [KeyboardButton("📒 Мои заметки"), KeyboardButton("ℹ️ Помощь")]
    ], resize_keyboard=True)

def get_cancel_menu():
    """Меню для отмены (если нужно отдельное)"""
    return ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True)