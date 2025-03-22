import os
import aiohttp
import asyncio
import aiofiles
from utils.server_logger import ServerLogger

async def download_model(model_path: str, model_url: str) -> bool:
    """
    Асинхронно скачивает модель из Google Drive, если она еще не существует
    
    Args:
        model_path (str): Путь, куда сохранить модель
        model_url (str): URL модели в Google Drive
    
    Returns:
        bool: True если модель успешно скачана или уже существует
    """
    logger = ServerLogger()
    
    # Проверяем, существует ли уже модель
    if os.path.exists(model_path):
        logger.info(f"Модель уже существует по пути: {model_path}")
        return True
    
    try:
        logger.info(f"Начинаем скачивание модели из {model_url}")
        
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Асинхронно скачиваем модель
        async with aiohttp.ClientSession() as session:
            async with session.get(model_url) as response:
                if response.status == 200:
                    # Асинхронная запись файла
                    async with aiofiles.open(model_path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024 * 1024)  # Читаем по 1MB
                            if not chunk:
                                break
                            await f.write(chunk)
                else:
                    logger.error(f"Ошибка при скачивании: статус {response.status}")
                    return False
        
        if os.path.exists(model_path):
            logger.info(f"Модель успешно скачана в {model_path}")
            return True
        else:
            logger.error("Ошибка при скачивании модели: файл не был создан")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при скачивании модели: {str(e)}")
        return False 