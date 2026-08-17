import os
import datetime
import subprocess
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secret")
DB_NAME = os.getenv("DB_NAME", "tozalash_db")

def create_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"{DB_NAME}_backup_{timestamp}.sql")
    
    # mysqldump buyrug'i (agar Windows bo'lsa mysqldump PATH da bo'lishi kerak)
    cmd = [
        "mysqldump",
        f"--host={DB_HOST}",
        f"--port={DB_PORT}",
        f"--user={DB_USER}",
        f"--password={DB_PASSWORD}",
        DB_NAME
    ]
    
    try:
        with open(backup_file, "w") as f:
            subprocess.run(cmd, stdout=f, check=True)
        logger.info(f"✅ Ma'lumotlar bazasi nusxasi saqlandi: {backup_file}")
        
        # Eski backuplarni o'chirish (masalan 7 kundan eskilarini)
        clean_old_backups(days=7)
    except Exception as e:
        logger.error(f"❌ Backup yaratishda xatolik: {e}")

def clean_old_backups(days: int):
    now = datetime.datetime.now().timestamp()
    for filename in os.listdir(BACKUP_DIR):
        file_path = os.path.join(BACKUP_DIR, filename)
        if os.path.isfile(file_path):
            if os.stat(file_path).st_mtime < now - days * 86400:
                os.remove(file_path)
                logger.info(f"🗑️ Eski backup o'chirildi: {filename}")

if __name__ == "__main__":
    create_backup()
