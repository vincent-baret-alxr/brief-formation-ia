FROM python:3.12.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace/module
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock
COPY . .
RUN mkdir -p /artifacts /workspace/module/artifacts \
    && chown -R 65532:65532 /artifacts /workspace/module

USER 65532:65532
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
