#!/bin/sh

# Ждем, пока база данных станет доступна
until nc -z db 5432; do
  echo "Waiting for database..."
  sleep 2
done

# Применяем миграции
alembic upgrade head

# Запускаем приложение
exec "$@"
