FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

RUN apt-get update \
    && apt-get upgrade --no-install-recommends --yes \
    && apt-get install --no-install-recommends --yes libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /usr/sbin/nologin appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py ./
COPY config ./config
COPY apps ./apps

RUN mkdir -p /app/media /app/staticfiles \
    && chown -R appuser:appuser /app/backend /app/media /app/staticfiles

USER appuser

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
