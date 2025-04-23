FROM python:3.11-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Установка переменной окружения
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "main.py"]
