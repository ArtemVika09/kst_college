"""
Скрипт для проверки подключения к Telegram API
"""
import os
import sys
from telegram import Bot
from telegram.error import TimedOut, NetworkError

TOKEN = os.getenv('BOT_TOKEN', '8387232890:AAGDhHOREkXmN58idiP8tgBWWLVF9mgCdZ8')

def check_connection():
    """Проверяет подключение к Telegram API"""
    print("=" * 50)
    print("🔍 ПРОВЕРКА ПОДКЛЮЧЕНИЯ К TELEGRAM API")
    print("=" * 50)
    
    try:
        print("📡 Подключение к Telegram API...")
        bot = Bot(token=TOKEN)
        
        # Пытаемся получить информацию о боте
        bot_info = bot.get_me()
        
        print("✅ Подключение успешно!")
        print(f"🤖 Имя бота: {bot_info.first_name}")
        print(f"👤 Username: @{bot_info.username}")
        print(f"🆔 ID бота: {bot_info.id}")
        print("=" * 50)
        return True
        
    except TimedOut:
        print("❌ ОШИБКА: Таймаут подключения")
        print("💡 Возможные причины:")
        print("   - Нет интернет-соединения")
        print("   - Telegram API заблокирован")
        print("   - Проблемы с прокси/файрволом")
        print("=" * 50)
        return False
        
    except NetworkError as e:
        print(f"❌ ОШИБКА: Проблема с сетью: {e}")
        print("💡 Проверьте интернет-соединение")
        print("=" * 50)
        return False
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        print("💡 Проверьте правильность токена бота")
        print("=" * 50)
        return False

if __name__ == "__main__":
    success = check_connection()
    sys.exit(0 if success else 1)

