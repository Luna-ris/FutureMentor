FROM python:3.11-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание и активация виртуального окружения
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Обновление pip в виртуальном окружении
RUN pip install --upgrade pip==25.0.1

# Установка рабочей директории
WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
# Установка numpy перед другими зависимостями
RUN pip install --no-cache-dir numpy<2.0.0
# Установка torch отдельно с CPU-индексом
RUN pip install --no-cache-dir torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu
# Установка остальных зависимостей
RUN pip install --no-cache-dir -r requirements.txt --timeout=100

# Копирование кода приложения
COPY . .

# Установка переменной окружения
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "main.py"]
