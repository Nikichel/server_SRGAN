import os
import gdown
from utils.server_logger import ServerLogger

async def download_model(model_path: str, model_url: str) -> bool:
    """Скачивание модели с Google Drive"""
    logger = ServerLogger()
    
    model_dir = os.path.dirname(model_path)
    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
        logger.info(f"Создана папка: {model_dir}")
    else:
        return True
    
    try:
        # Извлекаем идентификатор файла из URL
        file_id = model_url.split('/')[-2]
        
        # Формируем URL для скачивания
        download_url = f"https://drive.google.com/uc?id={file_id}"
        
        # Скачиваем файл
        gdown.download(download_url, model_path, quiet=False)
        
        logger.info(f"Модель успешно скачана и сохранена по пути: {model_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при скачивании модели: {e}")
        return False