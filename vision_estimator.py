"""
Tozalash Servis — Computer Vision AI & Cleaning Price Estimator
Gemini Vision + Pillow Image Optimization
Mebel, gilam, oyna va xona rasmlarini tahlil qilib narx smetasini avtomatik hisoblash
"""

import os
import io
import asyncio
from typing import Dict, Any, Optional
from loguru import logger
from PIL import Image

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from gemini_rotator import rotator


class VisionEstimator:
    """Mijoz yuborgan fotosuratlar asosida tozalash hajmi va narxini hisoblash"""

    def __init__(self):
        logger.info("👁️ Vision Estimator AI moduli yuklandi.")

    async def optimize_image(self, image_path: str, max_size: int = 1024) -> bytes:
        """Rasmni yuklashdan oldin siqish va optimallashtirish (WebP/JPEG)"""
        def _compress():
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85, optimize=True)
                return buffer.getvalue()

        return await asyncio.to_thread(_compress)

    async def estimate_from_image(
        self, image_path: str, language: str = "uz"
    ) -> Dict[str, Any]:
        """Fotosuratdan tozalash turi va narxini aniqlash"""
        if not os.path.exists(image_path):
            return self._fallback_estimation("Fayl topilmadi", language)

        try:
            image_bytes = await self.optimize_image(image_path)
            
            prompt = """
            Siz 'Tozalash Servis' kompaniyasining professional smeta baholovchisisiz.
            Ushbu rasmni diqqat bilan tahlil qiling va JSON formatida javob bering:
            {
                "service_type": "divan_yuvish" | "gilam_yuvish" | "standart_tozalash" | "remontdan_keyin" | "oyna_tozalash",
                "object_name": "3 o'rinli burchak divan / 12 kv.m gilam / 2 xonali uy",
                "estimated_quantity": 3.0,
                "unit": "o'rin" | "kv.m" | "xona",
                "stain_severity": "low" | "medium" | "high",
                "material_type": "matoli" | "teri" | "jun" | "sintetika",
                "details": "O'zbek tilida holat bo'yicha qisqacha xulosa (dog'lar, eskirish darajasi)",
                "recommended_price_min": 240000,
                "recommended_price_max": 300000
            }
            Faqat to'g'ri JSON qaytaring.
            """

            account = await rotator.get_active_account()
            if GENAI_AVAILABLE and account and account.is_available:
                genai.configure(api_key=account.key)
                model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                
                image_part = {
                    "mime_type": "image/jpeg",
                    "data": image_bytes
                }

                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: model.generate_content([prompt, image_part])
                )
                
                if response and response.text:
                    clean_json = response.text.strip()
                    if clean_json.startswith("```json"):
                        clean_json = clean_json[7:]
                    if clean_json.endswith("```"):
                        clean_json = clean_json[:-3]
                    
                    import json
                    data = json.loads(clean_json.strip())
                    logger.success(f"✅ Vision tahlili yakunlandi: {data.get('service_type')} -> {data.get('recommended_price_min')} UZS")
                    return data
        except Exception as e:
            logger.error(f"Vision tahlilida xatolik: {e}")

        return self._fallback_estimation("Standart baholash", language)

    def _fallback_estimation(self, reason: str, language: str) -> Dict[str, Any]:
        return {
            "service_type": "standart_tozalash",
            "object_name": "Xonadon yoki mebel",
            "estimated_quantity": 1.0,
            "unit": "xizmat",
            "stain_severity": "low",
            "material_type": "standart",
            "details": "Fotosurat qabul qilindi. Aniq narxni mutaxassisimiz joyida yoki qo'ng'iroq orqali tasdiqlaydi.",
            "recommended_price_min": 200000,
            "recommended_price_max": 500000
        }


# Global Instance
vision_estimator = VisionEstimator()
