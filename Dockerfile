FROM python:3.9-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY main.py .
COPY app.py .
COPY __init__.py .
COPY utils/ ./utils/
COPY transform/ ./transform/
COPY model/ ./model/

# Создание директории для логов
RUN mkdir -p logs/server

# Создание непривилегированного пользователя
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Команда запуска приложения
CMD ["python", "main.py"]