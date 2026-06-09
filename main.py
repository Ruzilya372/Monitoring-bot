# =====================================================================
# БЛОК 1: УНИВЕРСАЛЬНЫЙ СБОРЩИК ИЗ РАЗНЫХ ИСТОЧНИКОВ
# =====================================================================

import re
import feedparser
import pandas as pd
import config

print(" Подключаемся к пулу источников...")

rss_sources = {
    "Habr AI": "https://habr.com/ru/rss/hub/artificial_intelligence/all/?fl=ru",
    "Habr Big Data": "https://habr.com/ru/rss/hub/bigdata/all/?fl=ru",
}

parsed_posts = []

for source_name, url in rss_sources.items():
    try:
        print(f" Сканирую источник: {source_name}...")
        feed = feedparser.parse(url)
        if len(feed.entries) == 0:
            continue

        for entry in feed.entries:
            post_info = {
                "Источник": source_name,
                "Название": entry.title,
                "Описание": entry.summary if 'summary' in entry else "Нет описания",
                "Ссылка": entry.link,
                "Дата_публикации": entry.published if 'published' in entry else "Не указана"
            }
            parsed_posts.append(post_info)
    except Exception as e:
        print(f" Ошибка при чтении {source_name}: {e}")

if len(parsed_posts) > 0:
    df_rss = pd.DataFrame(parsed_posts)

    def clean_html(raw_html):
        if not isinstance(raw_html, str):
            return ""
        clean_text = re.sub(r'<[^>]+>', '', raw_html)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text

    df_rss['Очищенное_описание'] = df_rss['Описание'].apply(clean_html)
    print(f" Собрано всего постов: {len(df_rss)}")
else:
    print(" Ни один источник не отдал данные.")

# =====================================================================
# БЛОК 2: КОНФИГУРАЦИЯ И НАСТРОЙКИ МОНИТОРИНГА
# =====================================================================

# 1. ВВЕДИ СВОИ ДАННЫЕ ЗДЕСЬ СТРОГО В КАВЫЧКАХ:
TOKEN = config.TOKEN
CHAT_ID = config.CHAT_ID

# 2. Строгие правила фильтрации (без "ИИ" и "AI", чтобы не собирать мусор)
keywords = config.keywords

print(" Настройки успешно загружены в память!")

# =====================================================================
# БЛОК 3: ЛОГИЧЕСКИЙ ДВИЖОК (ФИЛЬТРАЦИЯ И ОТПРАВКА)
# =====================================================================
import requests

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f" Ошибка Telegram API: {response.text}")
    except Exception as e:
        print(f" Сбой сети: {e}")

print(" Запуск жесткой фильтрации...")

# Подготовка текста для поиска
df_rss['Текст_для_поиска'] = df_rss['Очищенное_описание'].str.lower() + " " + df_rss['Название'].str.lower()
search_pattern = "|".join([k.lower() for k in keywords])

# Фильтруем
df_rss['Это_целевое_мероприятие'] = df_rss['Текст_для_поиска'].str.contains(search_pattern, na=False)
final_events = df_rss[df_rss['Это_целевое_мероприятие'] == True]

print(f" Найдено реальных мероприятий: {len(final_events)} из {len(df_rss)}\n")

# Логика отправки
if len(final_events) > 0:
    print(f" Найдено совпадений: {len(final_events)}. Отправляю в Telegram...")
    for index, row in final_events.iterrows():
        short_description = row['Очищенное_описание'][:250] + "..." if len(row['Очищенное_описание']) > 250 else row['Очищенное_описание']

        template = f""" *НАЙДЕНО МЕРОПРИЯТИЕ:*

 *Название:* {row['Название']}
 *Источник:* {row['Источник']}
 *Описание:* {short_description}
 *Ссылка на мероприятие:* [Перейти на сайт]({row['Ссылка']})"""

        send_telegram_message(template)
else:
    print(" Настоящих хакатонов сейчас нет. Отправляю ОДНО тестовое сообщение для проверки новой архитектуры...")
    test_template = f""" *НАЙДЕНО МЕРОПРИЯТИЕ (ТЕСТ):*

 *Название:* Чистая архитектура в 3 блока!
 *Описание:* Спам побежден. Теперь бот будет присылать только реальные хакатоны, конкурсы и школы, не отвлекаясь на обычные статьи про ИИ.
 *Ссылка на мероприятие:* [Перейти на Хабр](https://habr.com/)"""

    send_telegram_message(test_template)