<p align="center">
  <img src="docs/screenshots/screenshot-1.png" width="32%" alt="Список операций">
  <img src="docs/screenshots/screenshot-2.png" width="32%" alt="Форма операции">
  <img src="docs/screenshots/screenshot-3.png" width="32%" alt="Справочники">
</p>


# Cash Flow Management

Демо-проект для управления денежными потоками на Django. Позволяет создавать, читать, обновлять и удалять транзакции с категориями и подкатегориями. Доступ к транзакциям есть как через кастомный UI, так и через админку Django (создание суперпользователя и авторизация не требуются).

## Стек

- Python 3.12
- Django 6
- Django REST Framework
- PostgreSQL 16
- Docker / Docker Compose

## Функционал

- Работа с данными через кастомный веб UI или админку Django - на выбор
- Полный CRUD всех моделей
- Валидация полей форм

## Быстрый запуск (docker compose)

```bash
make up
```

Команда создаёт `.env` из `.env.example` (если файл ещё не существует) и запускает приложение и PostgreSQL в Docker.

После запуска:

- приложение: <http://127.0.0.1:8000/>
- админка: <http://127.0.0.1:8000/admin/>

## Переменные окружения в .env.example

| Переменная | Описание |
| ------------ | ---------- |
| `SECRET_KEY` | Секретный ключ Django |
| `DEBUG` | Режим отладки (`True` / `False`) - при False для входа в админку надо будет создать суперпользователя |
| `ALLOWED_HOSTS` | Разрешённые хосты, через запятую |
| `POSTGRES_DB` | Имя базы данных |
| `POSTGRES_USER` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL |
| `POSTGRES_HOST` | Хост БД |
| `POSTGRES_PORT` | Порт PostgreSQL |

## Команды Makefile

| Команда | Описание |
| --------- | ---------- |
| `make up` | Создать `.env` и запустить Docker Compose |
| `make env` | Создать `.env` из `.env.example` |
| `make lint` | Проверить стиль кода (Ruff) |
| `make format` | Автоформатирование кода |
| `make pre-commit-install` | Установить git-хук для проверки при коммите |