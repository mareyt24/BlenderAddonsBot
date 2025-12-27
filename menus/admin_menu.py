from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_menu():
    """Меню администратора"""
    keyboard = [
        [InlineKeyboardButton("📦 Управление аддонами", callback_data="admin_addons")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
        # Убрали только "🏠 Главное меню"
    ]
    return InlineKeyboardMarkup(keyboard)

def get_addon_management_menu():
    """Меню управления аддонами"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить аддон", callback_data="admin_add_addon")],
        [InlineKeyboardButton("✏️ Редактировать аддон", callback_data="admin_edit_addon")],
        [InlineKeyboardButton("🗑️ Удалить аддон", callback_data="admin_delete_addon")],
        [InlineKeyboardButton("➕ Добавить категорию", callback_data="admin_add_category")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin")]  # Кнопка назад в админ-меню
    ]
    return InlineKeyboardMarkup(keyboard)

def get_addon_management_menu():
    """Меню управления аддонами"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить аддон", callback_data="admin_add_addon")],
        [InlineKeyboardButton("✏️ Редактировать аддон", callback_data="admin_edit_addon")],
        [InlineKeyboardButton("🗑️ Удалить аддон", callback_data="admin_delete_addon")],
        [InlineKeyboardButton("➕ Добавить категорию", callback_data="admin_add_category")],
        [InlineKeyboardButton("📊 Статистика по аддону", callback_data="admin_addon_stats")],  # Новая кнопка
        [InlineKeyboardButton("🔙 Назад", callback_data="admin")]
    ]
    return InlineKeyboardMarkup(keyboard)