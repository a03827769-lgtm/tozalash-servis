import os
import sys
import asyncio
from huggingface_hub import snapshot_download
from loguru import logger

MODEL_REPO = "aisha-org/navoiy-tts"
DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "navoiy_tts"
)


def check_cuda():
    try:
        import torch

        if torch.cuda.is_available():
            logger.info(f"✅ CUDA yoniq. GPU: {torch.cuda.get_device_name(0)}")
            return True
        else:
            logger.warning(
                "⚠️ PyTorch o'rnatilgan, lekin CUDA ishlamayapti (CPU rejim)."
            )
            return False
    except ImportError:
        logger.error("❌ PyTorch o'rnatilmagan!")
        return False


async def download_navoiy_model():
    logger.info("📦 Navoiy TTS modelini yuklab olish boshlandi...")
    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        # Asosiy model fayllarini yuklab olish
        path = snapshot_download(
            repo_id=MODEL_REPO, local_dir=DATA_DIR, ignore_patterns=["*.md", "demo/*"]
        )
        logger.info(f"✅ Model muvaffaqiyatli yuklandi: {path}")
    except Exception as e:
        logger.error(f"❌ Modelni yuklab olishda xatolik: {e}")


if __name__ == "__main__":
    logger.info("🚀 Navoiy TTS Setup ishga tushdi")
    has_cuda = check_cuda()

    if not has_cuda:
        logger.warning("CUDA yo'qligi sababli model CPU da juda sekin ishlashi mumkin.")

    asyncio.run(download_navoiy_model())
