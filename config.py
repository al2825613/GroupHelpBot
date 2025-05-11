import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # إعدادات أساسية
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMINS = list(map(int, os.getenv("ADMINS").split(","))) if os.getenv("ADMINS") else []
    
    # إعدادات الحماية
    BANNED_WORDS = os.getenv("BANNED_WORDS", "").split(",")
    MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", 3))
    ANTISPAM_LIMIT = int(os.getenv("ANTISPAM_LIMIT", 5))  # عدد الرسائل في فترة زمنية
    
    # إعدادات المجموعة
    REQUIRED_CHANNELS = os.getenv("REQUIRED_CHANNELS", "").split(",")
    WELCOME_MESSAGE = os.getenv("WELCOME_MESSAGE", "مرحباً بك في المجموعة!")
    
    # إعدادات الترجمة
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ar")
    SUPPORTED_LANGS = ["ar", "en", "fr", "es", "ru"]
    
    # إعدادات قاعدة البيانات
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")
    
    # إعدادات النسخ الاحتياطي
    BACKUP_INTERVAL = int(os.getenv("BACKUP_INTERVAL", 86400))  # ثانية (يومياً)
