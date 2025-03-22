# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app/ ./app/

# Создаем директории для логов и моделей
RUN mkdir -p logs/server logs/client models

# Создаем пользователя без прав root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Устанавливаем переменную окружения для пути к модели
ENV MODEL_PATH=/app/models/gen_and_disc_V5.pth

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["python", "-m", "app.main"] 