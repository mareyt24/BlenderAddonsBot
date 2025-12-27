# file: utils/youtube.py
import aiohttp
import asyncio
import re
import json
from typing import Optional, Tuple


# ==================== ПОЛУЧЕНИЕ ID ВИДЕО ====================
def get_video_id(youtube_url: str) -> Optional[str]:
    """
    Извлекает ID видео из ссылки YouTube.
    Возвращает строку с ID или None.
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([\w\-]{11})',
        r'(?:youtu\.be\/)([\w\-]{11})',
        r'(?:youtube\.com\/embed\/)([\w\-]{11})',
        r'(?:youtube\.com\/shorts\/)([\w\-]{11})',
        r'(?:youtube\.com\/v\/)([\w\-]{11})'  # NEW: ещё один возможный формат
    ]

    for pattern in patterns:
        match = re.search(pattern, youtube_url, re.IGNORECASE)  # FIXED: игнорируем регистр
        if match:
            video_id = match.group(1)
            print(f"✅ Извлечён Video ID: {video_id}")
            return video_id

    print("❌ Не удалось извлечь Video ID из ссылки.")
    return None


# Создаём алиас для обратной совместимости
extract_video_id = get_video_id


# ==================== МЕТОД 1: Noembed API (с исправленным парсингом) ====================
async def get_title_noembed(video_id: str) -> Optional[str]:
    """
    Пытается получить название через сервис Noembed.
    Простой и часто работает. Теперь корректно обрабатывает text/javascript.
    """
    url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*'  # FIXED: принимаем и text/javascript
    }

    try:
        # FIXED: увеличиваем таймаут и не проверяем строго MIME-тип
        timeout = aiohttp.ClientTimeout(total=15)
        connector = aiohttp.TCPConnector(ssl=False)  # Может помочь при проблемах с SSL

        async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
        ) as session:
            async with session.get(url) as response:
                response_text = await response.text()

                # FIXED: пытаемся распарсить ответ, даже если MIME-тип не application/json
                try:
                    data = json.loads(response_text)
                    title = data.get('title')
                    if title:
                        print(f"✅ Noembed вернул название: {title[:60]}...")
                        return str(title).strip()
                except json.JSONDecodeError as e:
                    # Если это не JSON, ищем title в тексте ответа (на всякий случай)
                    print(f"⚠️ Noembed вернул не JSON, а текст. Пытаемся найти заголовок вручную...")
                    # Простая попытка найти "title" в тексте
                    title_match = re.search(r'"title"\s*:\s*"([^"]+)"', response_text)
                    if title_match:
                        title = title_match.group(1)
                        print(f"✅ Нашли заголовок вручную: {title[:60]}...")
                        return title
                    else:
                        print(f"❌ Не удалось найти заголовок в ответе Noembed.")

    except asyncio.TimeoutError:
        print(f"❌ Noembed: таймаут запроса (15 сек).")
    except Exception as e:
        print(f"❌ Noembed не сработал: {type(e).__name__}: {e}")

    return None


# ==================== МЕТОД 2: Invidious API (ЗАПАСНОЙ, часто доступен) ====================
async def get_title_invidious(video_id: str) -> Optional[str]:
    """
    NEW: Альтернативный метод через публичные инстансы Invidious.
    Эти инстансы часто остаются доступными при блокировках.
    """
    # Список публичных инстансов (может меняться)
    invidious_instances = [
        "https://inv.riverside.rocks",
        "https://invidious.snopyta.org",
        "https://yewtu.be",
        "https://invidious.xyz",
        "https://invidiou.site"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }

    for instance in invidious_instances:
        api_url = f"{instance}/api/v1/videos/{video_id}"
        print(f"🔄 Invidious: пробуем инстанс {instance}...")

        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        title = data.get('title')
                        if title:
                            print(f"✅ Invidious ({instance}) вернул название: {title[:60]}...")
                            return str(title).strip()
                    else:
                        print(f"⚠️ Invidious ({instance}): статус {response.status}")
        except Exception as e:
            print(f"⚠️ Invidious ({instance}) не сработал: {type(e).__name__}")
            continue  # Пробуем следующий инстанс

    print("❌ Все инстансы Invidious недоступны.")
    return None


# ==================== ОСНОВНАЯ ФУНКЦИЯ (ОБНОВЛЁННАЯ) ====================
async def get_youtube_title(youtube_url: str, check_blender: bool = True) -> Tuple[Optional[str], bool]:
    """
    Основная функция. Пытается получить название видео разными способами.

    Возвращает:
        tuple: (название_видео_или_None, прошло_ли_проверку_на_blender)
    """
    print(f"\n{'=' * 60}")
    print(f"🔍 Анализ ссылки: {youtube_url}")

    # 1. Извлекаем ID видео
    video_id = get_video_id(youtube_url)
    if not video_id:
        return None, False

    # 2. Пробуем получить название разными способами (NEW: порядок изменён)
    title = None
    methods = [
        ("Noembed API", get_title_noembed),
        ("Invidious API", get_title_invidious),  # NEW: добавляем этот метод
    ]

    for method_name, method_func in methods:
        print(f"\n🔄 Пробую {method_name}...")
        title = await method_func(video_id)
        if title:
            print(f"✅ Успех с методом: {method_name}")
            break
        print(f"❌ Метод {method_name} не сработал")

    # 3. Если название не получено
    if not title:
        print("❌ Все методы не сработали. Не удалось получить название.")
        return None, False

    # 4. Проверка на слово "blender" или "блендер" (если нужно)
    if check_blender:
        title_lower = title.lower()
        has_blender = 'blender' in title_lower or 'блендер' in title_lower

        if has_blender:
            print(f"✅ Проверка пройдена: название содержит 'blender' или 'блендер'")
            return title, True
        else:
            print(f"❌ Проверка не пройдена: в названии нет слова 'blender' или 'блендер'")
            print(f"   Полное название: {title}")
            return title, False

    # Если проверка не требуется
    print(f"✅ Название получено (без проверки на Blender): {title[:80]}...")
    return title, True


# ==================== ФУНКЦИЯ ДЛЯ ОБРАБОТЧИКА СООБЩЕНИЙ ====================
async def get_video_info(youtube_url: str) -> Tuple[bool, str]:
    """
    Упрощённая обёртка для обработчика сообщений.
    Возвращает (успех, результат).
    В случае ошибки результат — это строка для отправки пользователю.
    """
    print(f"\n🎬 Запрос информации о видео: {youtube_url}")
    title, has_blender = await get_youtube_title(youtube_url, check_blender=True)

    if not title:
        error_msg = (
            "❌ **Не удалось получить название видео.**\n\n"
            "Возможные причины:\n"
            "• Видео является приватным или было удалено\n"
            "• Проблемы с доступом к YouTube из вашего региона\n"
            "• Некорректная ссылка\n\n"
            "**Попробуйте:**\n"
            "1. Проверить, открывается ли видео в браузере\n"
            "2. Использовать другую ссылку на это же видео\n"
            "3. Добавить видео позже"
        )
        return False, error_msg

    if not has_blender:
        # FIXED: экранируем возможные Markdown-символы в названии для Telegram
        safe_title = title.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
        error_msg = (
            f"❌ **Видео не связано с Blender.**\n\n"
            f"🎬 **Название:** {safe_title}\n\n"
            f"Чтобы добавить видео, его **название должно содержать слово 'blender' или 'блендер'**.\n"
            f"Если это действительно видео про Blender, переименуйте его на YouTube или выберите другое видео."
        )
        return False, error_msg

    return True, title  # В случае успеха возвращаем просто строку с названием


# ==================== ТЕСТОВЫЙ ЗАПУСК ====================
async def test():
    """Функция для тестирования работы модуля."""
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley
        "https://youtu.be/dQw4w9WgXcQ",  # Короткая ссылка
        "https://www.youtube.com/shorts/Y7bE9u0QP44",  # Короткое видео
    ]

    for url in test_urls:
        print(f"\n{'=' * 60}")
        print(f"🧪 ТЕСТ: {url}")
        success, result = await get_video_info(url)
        print(f"Успех: {success}")
        print(f"Результат: {result}")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        url = sys.argv[1]
        print("🧪 Запуск теста для одной ссылки...")
        result = asyncio.run(get_video_info(url))
        print(f"\n🎯 Результат: {result}")
    else:
        print("ℹ️  Для теста передайте ссылку как аргумент командной строки.")
        print("Пример: python youtube.py https://youtu.be/Y7bE9u0QP44")
        # Запускаем общий тест
        asyncio.run(test())