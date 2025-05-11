import sqlite3
import json
from datetime import datetime, timedelta
from config import Config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE_URL.split("///")[1])
        self._create_tables()
    
    def _create_tables(self):
        c = self.conn.cursor()
        
        # المستخدمون
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            language TEXT DEFAULT ?,
            is_subscribed BOOLEAN DEFAULT 0,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""", (Config.DEFAULT_LANGUAGE,))
        
        # المجموعات
        c.execute("""CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            title TEXT,
            settings TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # التحذيرات
        c.execute("""CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            admin_id INTEGER,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(chat_id) REFERENCES chats(chat_id)
        )""")
        
        # الحظورات
        c.execute("""CREATE TABLE IF NOT EXISTS bans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            admin_id INTEGER,
            duration INTEGER,  # بالثواني
            reason TEXT,
            is_permanent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(chat_id) REFERENCES chats(chat_id)
        )""")
        
        self.conn.commit()
    
    # ... (جميع الدوال السابقة مع تحسينات)
    
    async def get_chat_settings(self, chat_id: int):
        c = self.conn.cursor()
        c.execute("SELECT settings FROM chats WHERE chat_id = ?", (chat_id,))
        result = c.fetchone()
        return json.loads(result[0]) if result else {}
    
    async def update_chat_settings(self, chat_id: int, settings: dict):
        c = self.conn.cursor()
        c.execute("""INSERT OR REPLACE INTO chats (chat_id, settings)
                  VALUES (?, ?)""", (chat_id, json.dumps(settings)))
        self.conn.commit()
