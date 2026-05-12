# TaskFlow — платформа для управления задачами

## Цель проекта

Продемонстрировать production‑ready микросервисную архитектуру на Python с использованием 
FastAPI, PostgreSQL, Redis, Docker и современных инструментов разработки (uv, ruff, pre‑commit, GitHub Actions).

---

## Структура монорепозитория

taskflow-platform/
├── apps/                              # Сервисы
│   ├── api_gateway/                   # API Gateway (порт 8000)
│   ├── user_service/                  # Управление пользователями (8001)
│   ├── task_service/                  # Управление задачами (8002)
│   ├── notification_service/          # Уведомления (8003)
│   └── analytics_service/             # Аналитика (8004)
├── libs/
│   └── common/                        # Общая библиотека
│       ├── src/common/
│       │   ├── config.py              # Pydantic настройки (вложенные)
│       │   ├── logger_config.py       # Настройка structlog
│       │   └── models.py              # Базовые DTO (NotificationDTO и др.)
├── docker/
│   └── python-service.Dockerfile      # Универсальный Dockerfile для всех сервисов
├── .github/workflows/
│   └── ci.yml                         # CI/CD: линт, тесты (≥60%), сборка образов
├── .pre-commit-config.yaml            # Хуки: ruff, detect-secrets
├── .env.shared.example                # Шаблон переменных окружения
├── docker-compose.yml                 # Оркестрация всех сервисов + БД
├── pyproject.toml                     # UV workspace + ruff + pytest
└── uv.lock                            # Единый lock‑файл для всего проекта

---

## Запуск проекта

### Запустите всё через Docker Compose
bash
docker compose up -d

Что произойдёт:
- Поднимутся контейнеры PostgreSQL (порт 5438 на хосте) и Redis (6379)
- Запустяться сервисы миграций
- Каждый сервис выполнит `alembic upgrade head` (миграции)
- Запустятся 5 FastAPI приложений на портах 8000‑8004

### Проверьте работоспособность
bash
curl http://localhost:8000/health                # API Gateway
curl http://localhost:8001/health                # User Service
и т.д

---

##  Ключевые реализованные фичи

### 1. Централизованная конфигурация
- Файл `libs/common/src/common/config.py` содержит вложенные Pydantic модели (`DatabaseSettings`, `RedisSettings`, `ServiceUrls`).
- Переменные окружения используют двойное подчёркивание для вложенности:  
  `DATABASE__URL=postgresql+asyncpg://...`, `REDIS__PASSWORD=...`
- В тестовом режиме (`TESTING=true`) настройки не загружаются – используется SQLite.

### 2. Логирование уровня production
- `logger_config.py` настраивает `structlog`:  
  - в development – человеко‑читаемый вывод в консоль  
  - в production – JSON‑формат (легко парсить в Loki / Datadog)
- Фильтр `HealthCheckFilter` убирает шум от `/health` при `debug=False`
- Пример лога:
  {"event": "user.registered", "email": "user@example.com", "level": "info", "timestamp": "2026-05-12T10:15:30.123Z"}
  

### 3. Абстракция провайдеров уведомлений
- Базовый класс `NotificationProvider` (файл `base_notification_provider.py`) с методами `send()` и `validate_config()`.
- Реализован `EmailProvider` через `aiosmtplib`. Message‑ID генерируется детерминированно через `hashlib.sha256` + timestamp.
- Реестр провайдеров `AVAILABLE_PROVIDERS` в `router.py` позволяет легко добавлять новые каналы (Slack, Discord).

### 4. Тестирование с порогом покрытия 60%
- Тесты лежат в `apps/*/tests/*`, используют `pytest-asyncio`, фикстуры поднимают SQLite in‑memory.

### 5. Docker‑сборка с layer caching
- Единый `python-service.Dockerfile` принимает `APP_NAME` и копирует только нужную директорию `apps/${APP_NAME}`.
- Сборка в два этапа (`builder` → `runtime`) уменьшает финальный образ.
- Пример для user_service:
  COPY apps/user_service/pyproject.toml ./apps/user_service/
  RUN uv sync --frozen --no-dev --package user_service

### 6. CI/CD (GitHub Actions)
- `ci.yml` выполняет матричный прогон тестов по всем 5 сервисам.
- Отдельные стадии: `lint` (ruff check/format, conventional‑commits), `test` (pytest + покрытие), `docker-build` (имитация push в GHCR).
- Кэширование слоёв Docker через `type=gha`.

### 7. Git‑хуки (pre‑commit)
- `ruff` – авто‑исправление и форматирование.
- `detect-secrets` – проверка на наличие секретов.

### 8. API Gateway (единая точка входа)
- Маршрутизация запросов к внутренним сервисам на основе URL.
- Прокси‑вызовы через `httpx.AsyncClient` с таймаутом 30 секунд.
- Перехват и логирование входящих запросов и ответов.
- Единый health‑check endpoint (`/health`), агрегирующий статус зависимостей.
- Обработка ошибок с сохранением цепочки исключений .

### 9. User Service (аутентификация и профили)
- Регистрация, логин, выдача JWT (RS256, пары `private.pem`/`public.pem`).
- Хеширование паролей через `bcrypt`.
- Эндпоинты: `/register/`, `/login/`, `/refresh/`, `/users/me`, `/recive_user_by_id/{user_id}`.
- Фикстуры в тестах генерируют реальные сертификаты для JWT, а не мокают `jwt.decode`.

### 10. Task Service (бизнес‑логика задач)
- CRUD задач: создание, чтение, обновление статуса, назначение исполнителя.
- При назначении исполнителя автоматически вызывается `send_assign_notification`, которая через API Gateway отправляет уведомление.
- Асинхронная работа с БД через SQLAlchemy.
- Проверка существования автора через вызов User Service.

---

## 🔧 Примеры использования (API)

### Регистрация пользователя
curl -X POST http://localhost:8000/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "secret"}'

### Логин (получение JWT)
curl -X POST http://localhost:8000/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "secret"}'
# → {"access_token": "...", "refresh_token": "...", "user_id": 1}


### Создание задачи (через API Gateway)
curl -X POST http://localhost:8000/create_task/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Документация", "content": "Написать README", "author_id": 1}'

### Назначить исполнителя (триггер уведомления по email)
curl -X POST http://localhost:8000/assign_a_worker/?task_id=1&author_id=2 \
  -H "Authorization: Bearer <access_token>"
→ Сервис уведомлений отправляет письмо на email назначенного пользователя.

### Отправить уведомление напрямую (для отладки)
curl -X POST http://localhost:8000/tasks/send_notification/ \
  -H "Content-Type: application/json" \
  -d '{"recipient": "alice@example.com", "provider": "email", "subject": "Hello", "message": "Task assigned"}'

### Получить аналитику по задачам (агрегация)
curl http://localhost:8004/stats?period=week

---

## 📄 Лицензия

MIT — проект исключительно учебный. Реальные пароли (SMTP, Redis) должны храниться в `.env`, который добавлен в `.gitignore`.
