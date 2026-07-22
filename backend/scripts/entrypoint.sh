#!/bin/sh
set -e

if [ "$RUN_MIGRATIONS" != "false" ]; then
  echo "Aplicando migrations..."
  python manage.py migrate --noinput
fi

if [ "$RUN_SEED" != "false" ]; then
  echo "Rodando seed (idempotente)..."
  python manage.py seed
fi

exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
