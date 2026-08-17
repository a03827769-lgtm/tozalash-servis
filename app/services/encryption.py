from cryptography.fernet import Fernet
from app.core.config import settings


class EncryptionService:
    def __init__(self):
        # In a real app, load this from environment variables
        self.key = getattr(settings, "ENCRYPTION_KEY", Fernet.generate_key())
        self.cipher = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(encrypted_data.encode()).decode()


encryption_service = EncryptionService()
