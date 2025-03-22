import numpy as np
import torch
from .generator import Generator
from transform.transform import Transforms
import io
from PIL import Image
import base64
from typing import Optional
from utils.server_logger import ServerLogger
from utils.download_model import download_model
import os

class SRGANWrapper:
    def __init__(self):
        """Инициализация обертки для модели SRGAN"""
        self.logger = ServerLogger()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = Generator(in_channels=3).to(self.device)
        self.transform = Transforms()
        self.ready = False
        self.model_path = "/app/models/gen_and_disc_V5.pth"
        self.model_url = "https://drive.google.com/file/d/1EgdyWXjGPq-nuM1q3KBURCa0pPlQSpvx/view?usp=sharing"
        self.logger.info(f"Initialized SRGAN wrapper on device: {self.device}")
    
    async def load_model(self) -> bool:
        """Загрузка модели SRGAN"""
        try:
            # Скачиваем модель, если она еще не существует
            if not await download_model(self.model_path, self.model_url):
                self.logger.error("Не удалось скачать модель")
                return False
            print("load start")
            # Загружаем модель
            checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
            print("load complited")
            self.model.load_state_dict(checkpoint["generator_state_dict"])
            
            self.model.eval()
            self.ready = True
            self.logger.info("Модель SRGAN успешно загружена")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке модели SRGAN: {e}")
            self.ready = False
            return False
    
    async def upscale_image(self, image_data: bytes, scale_factor: int = 4) -> Optional[str]:
        """Увеличение разрешения изображения с помощью SRGAN"""
        print(self.ready)
        print(self.model)
        if not self.ready or self.model is None:
            self.logger.error("Model not loaded")
            raise RuntimeError("Модель SRGAN не загружена")

        try:
            self.logger.log_image_processing(len(image_data), None)
            
            if len(image_data) == 0:
                raise ValueError("Получены пустые данные изображения")
            
            image_bytes = io.BytesIO(image_data)
            image_bytes.seek(0)
            
            try:
                img = Image.open(image_bytes)
                img = img.convert('RGB')
                self.logger.debug(f"Image opened: format={img.format}, mode={img.mode}")
            except Exception as img_error:
                self.logger.log_error(img_error, "image_opening")
                raise
            
            img_array = np.array(img)
            self.logger.debug(f"Image converted to array: shape={img_array.shape}")
            
            if img_array.shape[0] > 500 or img_array.shape[1] > 500:
                raise ValueError("Большое изображение")

            # Остальной код без изменений
            pre_image = await self.preprocessing(img_array)
            
            with torch.no_grad():
                SR_image = self.model(pre_image)
            
            SR_image = await self.postprocessing(SR_image)
            
            result_img = Image.fromarray((SR_image * 255).astype(np.uint8))
            buffer = io.BytesIO()
            result_img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            return img_str
        except Exception as e:
            self.logger.log_error(e, "upscale_image")
            return None

    async def postprocessing(self, SR_image):
        SR_image = SR_image.squeeze(0).permute(1, 2, 0).cpu().numpy()
        SR_image= np.clip(SR_image, -1, 1)
        SR_image = SR_image * 0.5 + 0.5

        SR_image = np.clip(SR_image, 0, 1)

        # SR_image = cv2.bilateralFilter(SR_image, d=3, sigmaColor=75, sigmaSpace=75)
        return SR_image
    
    async def preprocessing(self, low_image):
        # Преобразуем изображение с помощью albumentations
        #low_transform = await self.transform.get_lowres_transform(low_image.shape)
        #preproc_image = low_transform(image=low_image)["image"]

        preproc_image = self.transform.original_transform(image=low_image)["image"]
        # Добавляем batch dimension и перемещаем на устройство (GPU/CPU)
        preproc_image = preproc_image.unsqueeze(0).to(self.device)

        return preproc_image
        
    def is_ready(self) -> bool:
        """Проверка готовности модели"""
        return self.ready 