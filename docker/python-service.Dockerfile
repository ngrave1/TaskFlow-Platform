FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

ARG APP_NAME

COPY pyproject.toml uv.lock ./
COPY libs/common/ ./libs/common/
COPY apps/${APP_NAME}/ ./apps/${APP_NAME}/

RUN uv pip install --system --no-cache-dir -e ./libs/common
RUN cd apps/${APP_NAME} && uv pip install --system --no-cache-dir -e .

ENV PYTHONPATH=/app:/app/apps/${APP_NAME}/src:/app/libs/common/src

EXPOSE 8000

CMD ["sh", "-c", "SERVICE_NAME=$(echo ${APP_NAME} | tr - _) && uvicorn apps.${SERVICE_NAME}.src.${SERVICE_NAME}.main:app --host 0.0.0.0 --port 8000"]