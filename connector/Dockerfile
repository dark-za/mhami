FROM python:3.13-slim

# H-04: run as a non-root user, no Docker socket, minimal surface.
RUN groupadd --system --gid 1001 mhami \
    && useradd --system --uid 1001 --gid mhami mhami

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/

USER mhami
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
