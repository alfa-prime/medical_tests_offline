.PHONY: up down bash logs clear-volume up-prod down-prod logs-prod bash-prod clean init_db
# connect .env file
include .env
export

# --- Development ---
up:
	docker compose up --build -d

down:
	docker compose down

bash:
	docker exec -it ${DEV_CONTAINER_NAME} bash

logs:
	docker compose logs -f app

# --- Production ---
up-prod:
	docker compose -f docker-compose.prod.yml up --build -d

down-prod:
	docker compose -f docker-compose.prod.yml down

logs-prod:
	docker compose -f docker-compose.prod.yml logs -f app

bash-prod:
	docker exec -it ${PROD_CONTAINER_NAME} bash

# --- Common ---
# Создает и применяет САМУЮ ПЕРВУЮ миграцию.
# Выполняется один раз при инициализации проекта.
init_db:
	docker compose -f docker-compose.prod.yml exec app \
	bash -c "alembic revision --autogenerate -m 'init' && alembic upgrade head"


# --- System Cleanup ---
clear-volume:
	@read -p "Вы уверены, что хотите удалить том ${DEV_CONTAINER_NAME}_postgres_data? ВСЕ ДАННЫЕ БУДУТ ПОТЕРЯНЫ. [y/N] " choice; \
	if [ "$$choice" = "y" ]; then \
		docker compose down && docker volume rm ${DEV_CONTAINER_NAME}_postgres_data; \
	else \
		echo "Отменено."; \
	fi

# "Мягкая" очистка: удаляет остановленные контейнеры и "висящие" образы
prune:
	docker system prune -f

# "Жесткая" очистка: удаляет ВСЁ неиспользуемое (образы, контейнеры, тома)
clean:
	@read -p "Вы уверены, что хотите удалить ВСЕ неиспользуемые контейнеры, образы и тома на всей системе? [y/N] " choice; \
	if [ "$$choice" = "y" ]; then \
		docker system prune -a --volumes -f; \
	else \
		echo "Отменено."; \
	fi
