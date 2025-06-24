.PHONY: start stop restart build logs clean migrate create-migration seed seed-fresh help

# Comando principal para iniciar el entorno de desarrollo
start:
	docker-compose up -d

# Detener los contenedores
stop:
	docker-compose down

# Reiniciar los contenedores
restart:
	docker-compose restart

# Construir las imágenes
build:
	docker-compose build

# Ver los logs de los contenedores
logs:
	docker-compose logs -f

# Limpiar contenedores, volúmenes e imágenes
clean:
	docker-compose down -v --rmi all --remove-orphans

# Ejecutar migraciones de la base de datos
migrate:
	docker-compose exec api bash -c "cd /app && uv run alembic -c app/alembic.ini upgrade head"

# Crear una nueva migración
create-migration:
	@read -p "Ingrese el mensaje para la migración: " message; \
	docker-compose exec api bash -c "cd /app && uv run alembic -c app/alembic.ini revision --autogenerate -m \"$$message\""

# Ejecutar seed de datos
seed:
	docker-compose exec api bash -c "cd /app && uv run python -m app.db.seed"

# Limpiar y recrear datos de seed
seed-fresh:
	docker-compose exec api bash -c "cd /app && uv run python -m app.db.seed clear"
	docker-compose exec api bash -c "cd /app && uv run python -m app.db.seed"

# Mostrar ayuda
help:
	@echo "Comandos disponibles:"
	@echo "  make start             - Iniciar el entorno de desarrollo"
	@echo "  make stop              - Detener los contenedores"
	@echo "  make restart           - Reiniciar los contenedores"
	@echo "  make build             - Construir las imágenes"
	@echo "  make logs              - Ver logs de los contenedores"
	@echo "  make clean             - Limpiar contenedores y volúmenes"
	@echo "  make migrate           - Ejecutar migraciones de la base de datos"
	@echo "  make create-migration  - Crear una nueva migración"
	@echo "  make seed              - Ejecutar seed de datos"
	@echo "  make seed-fresh        - Limpiar y recrear datos de seed"
	@echo "  make help              - Mostrar esta ayuda"

# Comando por defecto
.DEFAULT_GOAL := help 