# Makefile for managing Docker-based FastAPI app

# connect .env file
include .env
export


# --- Development ---
up:
	docker compose up --build

down:
	docker compose down

bash:
	docker exec -it ${DEV_CONTAINER_NAME} bash

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
