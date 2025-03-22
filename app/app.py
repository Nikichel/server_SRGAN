from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import Optional
import asyncio
import gc
from .model.srgan_wrapper import SRGANWrapper

class FastAPIApp:
    def __init__(self):
        self.app = FastAPI(title="SRGAN Upscaler API", 
                          description="API для увеличения разрешения изображений с использованием SRGAN",
                          version="1.0.0")
        
        # Подключение CORS для взаимодействия с фронтендом
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # В продакшене заменить на список конкретных доменов
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Инициализация компонентов
        self.srgan = SRGANWrapper()
        self.ready = False
        
        # Настройка маршрутов и событий
        self.setup_routes()
        
        # Регистрация обработчика завершения работы
        self.app.add_event_handler("shutdown", self.cleanup)
    
    async def load_model(self):
        """Асинхронная загрузка модели SRGAN"""
        try:
            await self.srgan.load_model()
            self.ready = True
            return True
        except Exception as e:
            self.ready = False
            raise RuntimeError(f"Ошибка при загрузке модели: {str(e)}")

    def is_ready(self):
        """Проверка готовности модели"""
        return self.ready and hasattr(self.srgan, 'model') and self.srgan.model is not None

    async def cleanup(self):
        """Очистка ресурсов при завершении работы сервера"""
        try:
            if hasattr(self, "srgan") and self.srgan.model:
                # Удаление модели
                del self.srgan.model
                self.srgan.model = None
                
                # Принудительный вызов сборщика мусора
                gc.collect()
                
                print("Ресурсы модели SRGAN успешно освобождены")
        except Exception as e:
            print(f"Ошибка при очистке ресурсов: {str(e)}")

    def setup_routes(self):
        
        @self.app.get("/")
        async def root_path():
            return {"status": "success", "response": "root"}
    
        # Маршрут для обработки изображений
        @self.app.post("/upscale")
        async def upscale_image(
            file: UploadFile = File(...),
            scale_factor: Optional[int] = Form(4)
        ):
            if not self.is_ready():
                raise HTTPException(
                    status_code=503,
                    detail="Сервис временно недоступен. Модель не загружена."
                )
            
            try:
                # Проверка типа файла
                if not file.content_type.startswith('image/'):
                    raise HTTPException(
                        status_code=400,
                        detail="Файл должен быть изображением"
                    )
                
                # Обработка изображения
                contents = await file.read()
                result = await self.srgan.upscale_image(contents, scale_factor)
                
                if not result:
                    raise HTTPException(
                        status_code=500,
                        detail="Ошибка при обработке изображения"
                    )
                
                return {"status": "success", "image": result}
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка при обработке запроса: {str(e)}"
                )
    
    def run(self, host="0.0.0.0", port=8000):
        """Запуск приложения"""
        uvicorn.run(self.app, host=host, port=port)

# Создание и запуск приложения, если модуль запущен напрямую
if __name__ == "__main__":
    app = FastAPIApp()
    app.run() 