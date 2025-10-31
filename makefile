# Makefile for managing Docker-based FastAPI app
.PHONY: up down bash logs clear-volume up-prod down-prod logs-prod bash-prod clean
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
	docker logs ${DEV_CONTAINER_NAME} -f

clear-volume:
	docker volume rm ${DEV_CONTAINER_NAME}_postgres_data

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
clean:
	docker system prune -a --volumes -f
