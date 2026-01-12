FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY libs/common/pyproject.toml ./libs/common/
COPY apps/user_service/pyproject.toml ./apps/user_service/

RUN uv pip install --system -e ./libs/common
RUN uv pip install --system -e ./apps/user_service

COPY libs/common ./libs/common
COPY apps/user_service ./apps/user_service


WORKDIR /app/apps/user_service

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "user_service.main:app", "--host", "0.0.0.0", "--port", "8000"]