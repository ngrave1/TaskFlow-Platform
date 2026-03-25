ARG APP_NAME

FROM python:3.12-slim as base

RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

RUN mv /root/.local/bin/uv /usr/local/bin/uv && \
    chmod +x /usr/local/bin/uv

WORKDIR /app

FROM base as builder
ARG APP_NAME

COPY pyproject.toml uv.lock ./
COPY libs/common/pyproject.toml ./libs/common/pyproject.toml
COPY apps/${APP_NAME}/pyproject.toml ./apps/${APP_NAME}/pyproject.toml

RUN uv sync --frozen --no-dev --package ${APP_NAME}

FROM base as runtime
ARG APP_NAME
ENV APP_NAME=${APP_NAME}

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml ./
COPY libs/common/ ./libs/common/
COPY apps/${APP_NAME}/ ./apps/${APP_NAME}/

ENV PYTHONPATH="/app:/app/apps/${APP_NAME}/src:/app/libs/common/src"

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser
EXPOSE 8000

CMD ["sh", "-c", "SERVICE_NAME=$(echo ${APP_NAME} | tr - _) && uvicorn apps.${SERVICE_NAME}.src.${SERVICE_NAME}.main:app --host 0.0.0.0 --port 8000"]