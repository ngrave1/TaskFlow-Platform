#!/bin/bash

set -e

wait_for_postgres() {
    local retries=30
    while [ $retries -gt 0 ]; do
        if PGPASSWORD="${POSTGRES_PASSWORD:-admin123}" psql \
            -h "${POSTGRES_HOST:-postgres}" \
            -p "${POSTGRES_PORT:-5432}" \
            -U "${POSTGRES_USER:-admin}" \
            -d "${POSTGRES_DB:-postgres}" \
            -c "SELECT 1" >/dev/null 2>&1; then
            echo "Postgres доступен"
            return 0
        fi
        
        sleep 2
        retries=$((retries - 1))
    done
    
    echo "Не удалось подключиться к Postgres"
    return 1
}

if [ "${APP_NAME}" = "user_service" ] || [ "${APP_NAME}" = "task_service" ]; then
    wait_for_postgres
    cd "/app/apps/${APP_NAME}"
    
    if alembic upgrade head; then
        echo "Миграции прокинуты для ${APP_NAME}"
        exit 0
    else
        echo "Не удалось применить миграции"
        exit 1
    fi
else
    echo "миграции не требуются"
    exit 0
fi