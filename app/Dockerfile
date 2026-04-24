# app/Dockerfile
FROM python:3.12-slim

# --------------------------------------------------
# Рабочая директория
# --------------------------------------------------
WORKDIR /app
ENV PYTHONPATH=/app

# --------------------------------------------------
# Системные зависимости для pyodbc
# --------------------------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    unixodbc \
    unixodbc-dev \
    libodbc2 \
    libodbcinst2 \
    odbcinst \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Установка Microsoft ODBC Driver (современный способ)
# --------------------------------------------------
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Python зависимости
# --------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------
# Копируем код
# --------------------------------------------------
COPY . .

# --------------------------------------------------
# Запуск FastAPI
# --------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]