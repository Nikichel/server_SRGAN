import asyncio
from app import FastAPIApp
import ngrok
import nest_asyncio
from utils.server_logger import ServerLogger
import uvicorn
import signal
import sys

class NGROKServer:
    def __init__(self):
        self.logger = ServerLogger()
        self.listener = None
        self.app = None
        self.auth_token = "2ufTHw5cqdduJXwhefZk0gsWf8e_FhFCjg718JVEijSLbmHD"
        
        # Применяем nest_asyncio для поддержки вложенных циклов событий
        nest_asyncio.apply()
        
        # Настраиваем обработчики сигналов для корректного завершения
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    async def init_app(self):
        """Асинхронная инициализация приложения"""
        self.logger.info("Инициализация приложения...")
        self.app = FastAPIApp()
        await self.app.load_model()
        self.logger.info("Приложение инициализировано успешно")
        return self.app

    async def start_ngrok_tunnel(self):
        """Запуск туннеля ngrok"""
        try:
            self.logger.info("Настройка ngrok...")
            ngrok.set_auth_token(self.auth_token)
            
            self.logger.info("Создание туннеля ngrok...")
            self.listener = await ngrok.connect(8000)
            public_url = self.listener.url()
            self.logger.info(f"Публичный URL: {public_url}")
            
            return public_url
        except Exception as e:
            self.logger.log_error(e, "ngrok_tunnel_start")
            raise

    async def close_ngrok_tunnel(self):
        """Закрытие туннеля ngrok"""
        if self.listener:
            try:
                self.logger.info("Закрытие туннеля ngrok...")
                await self.listener.close()
                self.logger.info("Туннель ngrok закрыт успешно")
            except Exception as e:
                self.logger.log_error(e, "ngrok_tunnel_close")

    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        self.logger.info(f"Получен сигнал {signum}. Начало завершения работы...")
        asyncio.create_task(self.cleanup())
        sys.exit(0)

    async def cleanup(self):
        """Очистка ресурсов при завершении"""
        self.logger.info("Начало очистки ресурсов...")
        await self.close_ngrok_tunnel()
        if hasattr(self.app, 'cleanup'):
            await self.app.cleanup()
        self.logger.info("Очистка ресурсов завершена")

    async def run_server(self):
        """Запуск сервера"""
        try:
            # Инициализация приложения
            self.app = await self.init_app()
            
            # Проверка готовности модели
            if not hasattr(self.app, 'ready') or not self.app.ready:
                raise RuntimeError("Модель не была успешно загружена")
            
            # Запуск туннеля ngrok
            public_url = await self.start_ngrok_tunnel()
            
            # Запуск сервера
            self.logger.info("Запуск сервера...")
            config = uvicorn.Config(
                app=self.app.app,
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            self.logger.log_error(e, "server_run")
            await self.cleanup()
            raise
        finally:
            await self.cleanup()

if __name__ == "__main__":
    server = NGROKServer()
    try:
        asyncio.run(server.run_server())
    except KeyboardInterrupt:
        print("\nПолучен сигнал прерывания. Завершение работы...")
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
    finally:
        # Убедимся, что все ресурсы освобождены
        if server.app:
            asyncio.run(server.cleanup())