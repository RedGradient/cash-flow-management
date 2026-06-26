.PHONY: env up down clean

# Создать .env из .env.example, если файл ещё не существует
env:
	@test -f .env || cp .env.example .env

# Запуск через Docker Compose (PostgreSQL + приложение)
up: env
	docker compose up --build

# Остановить контейнеры проекта
down:
	docker compose down

# Удалить контейнеры, volume с данными Postgres и образ проекта
clean:
	docker compose down --rmi local -v