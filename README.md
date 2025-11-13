# SMART Мебель — сайт на Flask

## Запуск
1. Python 3.10+
2. Установка зависимостей:
```
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```
3. Запуск:
```
python app.py
```
Откройте http://localhpython ost:5000

## Конфигурация
- WhatsApp, Instagram и домен в `app.py` (переменные окружения можно добавить позже).
- При первом запуске создастся SQLite база `site.db` с таблицей `leads`.

## Структура
- `templates/` — страницы (Jinja2)напишите в в в
- `static/` — стили, JS, медиа
- `app.py` — маршруты, сохранение заявок
