import json
import os

# Путь к файлу с данными аддонов
ADDONS_FILE = "../addons_data.json"

# Загружаем данные из файла
if os.path.exists(ADDONS_FILE):
    with open(ADDONS_FILE, 'r', encoding='utf-8') as f:
        ADDONS_DATA = json.load(f)
else:
    # Новая структура без разделов
    ADDONS_DATA = {
        "обучающие": [
            {
                "name": "Game Tools Pro",
                "description": "Инструменты для создания игр",
                "github": "https://github.com/example/game-tools",
                "youtube": "https://www.youtube.com/watch?v=example"
            }
        ],
        "визуализация": [
            {
                "name": "Render Optimizer",
                "description": "Оптимизация рендеринга",
                "github": "https://github.com/example/render-opt",
                "youtube": "https://www.youtube.com/watch?v=example3"
            }
        ]
    }
    # Сохраняем начальные данные
    with open(ADDONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ADDONS_DATA, f, ensure_ascii=False, indent=2)


def save_data():
    """Сохраняет данные в файл"""
    with open(ADDONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ADDONS_DATA, f, ensure_ascii=False, indent=2)


def get_categories():
    return list(ADDONS_DATA.keys())


def get_addons(category):
    return ADDONS_DATA.get(category, [])


def get_addon(category, index):
    addons = get_addons(category)
    return addons[index] if 0 <= index < len(addons) else None


def add_addon(category, name, description, github, youtube):
    """Добавление нового аддона (для админов)"""
    if category not in ADDONS_DATA:
        ADDONS_DATA[category] = []

    new_addon = {
        "name": name,
        "description": description,
        "github": github,
        "youtube": youtube
    }

    ADDONS_DATA[category].append(new_addon)
    save_data()
    print(f"✅ Добавлен новый аддон: {name} в {category}")
    return True


def update_addon(category, index, name=None, description=None, github=None, youtube=None):
    """Обновление аддона (для админов)"""
    addons = get_addons(category)
    if index < 0 or index >= len(addons):
        return False

    addon = addons[index]
    if name:
        addon["name"] = name
    if description:
        addon["description"] = description
    if github:
        addon["github"] = github
    if youtube:
        addon["youtube"] = youtube

    save_data()
    print(f"✅ Обновлен аддон: {addon['name']} в {category}")
    return True


def delete_addon(category, index):
    """Удаление аддона (для админов)"""
    addons = get_addons(category)
    if index < 0 or index >= len(addons):
        return False

    deleted_name = addons[index]["name"]
    ADDONS_DATA[category].pop(index)

    # Если в категории больше нет аддонов, удаляем категорию
    if not ADDONS_DATA[category]:
        del ADDONS_DATA[category]

    save_data()
    print(f"🗑️ Удален аддон: {deleted_name} из {category}")
    return True


def add_category(category):
    """Добавление новой категории (для админов)"""
    if category not in ADDONS_DATA:
        ADDONS_DATA[category] = []
        save_data()
        print(f"✅ Добавлена новая категория: {category}")
        return True
    print(f"⚠️ Категория уже существует: {category}")
    return False