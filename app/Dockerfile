# app/Dockerfile
FROM python:3.12-slim

# Корень проекта внутри контейнера
WORKDIR /app
ENV PYTHONPATH=/app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ⚠️ ВАЖНО: копируем ВЕСЬ build context (./app)
 COPY . .

# Запуск через пакет
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
