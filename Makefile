.PHONY: lint format typecheck pre-commit-install env up test coverage

# Проверка стиля кода (линт + форматирование без изменений)
lint:
	ruff check .
	ruff format --check .

# Автоформатирование кода
format:
	ruff format .

# Проверка типов (mypy + django-stubs)
typecheck:
	mypy .

# Установка git-хука: ruff check и ruff format при каждом коммите
pre-commit-install:
	pre-commit install

# Создать .env из .env.example, если файл ещё не существует
env:
	@test -f .env || cp .env.example .env

# Запуск через Docker Compose (PostgreSQL + приложение)
up: env
	docker compose up --build

# Запуск тестов (нужен PostgreSQL, см. POSTGRES_* в .env)
test:
	python manage.py test

# Тесты с отчётом покрытия
coverage:
	coverage run manage.py test
	coverage report
