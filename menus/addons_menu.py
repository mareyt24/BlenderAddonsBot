# file: menus/addons_menu.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from data.addons_data import get_categories, get_addons, get_addon

def get_categories_menu():
    keyboard = []
    for category in get_categories():
        keyboard.append([InlineKeyboardButton(category, callback_data=f"cat:{category}")])
    # Убрали только "🏠 Главное меню", оставили все остальное
    return InlineKeyboardMarkup(keyboard)

def get_addons_menu(category):
    keyboard = []
    addons = get_addons(category)

    for i, addon in enumerate(addons):
        keyboard.append([InlineKeyboardButton(addon["name"], callback_data=f"add:{category}:{i}")])

    keyboard.append([InlineKeyboardButton("🔙 К категориям", callback_data="cats")])
    # Убрали только "🏠 Главное меню", кнопка назад осталась
    return InlineKeyboardMarkup(keyboard)


# В addons_menu.py
# В addons_menu.py
def get_addon_details_menu(category, index, has_videos=None):
    addon = get_addon(category, index)

    keyboard = []
    if addon.get("github"):
        keyboard.append([InlineKeyboardButton("🔗 GitHub", url=addon["github"])])
    if addon.get("youtube"):
        keyboard.append([InlineKeyboardButton("📺 YouTube (официальный)", url=addon["youtube"])])

    keyboard.append([InlineKeyboardButton("🎬 Полезные видео", callback_data=f"videos:{category}:{index}")])
    keyboard.append([InlineKeyboardButton("🎬 Добавить видео", callback_data=f"add_video:{category}:{index}")])
    keyboard.append([InlineKeyboardButton("🔙 К аддонам", callback_data=f"cat:{category}")])

    return InlineKeyboardMarkup(keyboard)

    return InlineKeyboardMarkup(keyboard)
def get_videos_list_menu(videos, category, index):
    keyboard = []
    for video in videos:
        video_id = video[0]
        title = video[3]
        likes = video[5]
        dislikes = video[6]

        short_title = title[:25] + "..." if len(title) > 25 else title
        likes_text = f" 👍{likes}" if likes > 0 else ""
        dislikes_text = f" 👎{dislikes}" if dislikes > 0 else ""
        button_text = f"{short_title}{likes_text}{dislikes_text}"

        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"view_video:{video_id}")
        ])

    keyboard.append([
        InlineKeyboardButton("➕ Добавить видео", callback_data=f"add_video:{category}:{index}")
    ])
    keyboard.append([
        InlineKeyboardButton("🔙 Назад", callback_data=f"add:{category}:{index}")
    ])
    return InlineKeyboardMarkup(keyboard)  # Кнопка "Назад" осталась

def get_video_view_menu(video_id, category, index):
    keyboard = [
        [
            InlineKeyboardButton("👍", callback_data=f"like_video:{video_id}"),
            InlineKeyboardButton("👎", callback_data=f"dislike_video:{video_id}")
        ],
        [
            InlineKeyboardButton("🔙 К списку видео", callback_data=f"videos:{category}:{index}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)  # Кнопка "Назад" осталась

def get_add_video_menu(category, index):
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_add_video:{category}:{index}")]
    ]
    return InlineKeyboardMarkup(keyboard)