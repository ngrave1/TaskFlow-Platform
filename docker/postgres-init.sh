set -e
until pg_isready -U "${POSTGRES_USER:-postgres}"; do
    sleep 2
done
databases="user_service task_service notification_service analytics_service"
for db in $databases; do
    psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER:-postgres}" <<-EOSQL
        CREATE DATABASE $db;
        GRANT ALL PRIVILEGES ON DATABASE $db TO "${POSTGRES_USER:-postgres}";
EOSQL
done
echo "database created"