import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from ai_client import UnifiedFactGenerator
from live_location_manager import LiveLocationManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate environment variables
def validate_environment():
    """Validate that all required environment variables are set"""
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    openai_key = os.getenv('OPENAI_API_KEY')
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    
    if not telegram_token:
        logger.error("❌ TELEGRAM_TOKEN environment variable is not set!")
        logger.error("Please set TELEGRAM_TOKEN in your environment variables.")
        logger.error("In Railway: Go to your project → Variables tab → Add TELEGRAM_TOKEN")
        sys.exit(1)
    
    if not openai_key and not openrouter_key:
        logger.error("❌ Neither OPENAI_API_KEY nor OPENROUTER_API_KEY environment variable is set!")
        logger.error("Please set at least one of these in your environment variables.")
        logger.error("In Railway: Go to your project → Variables tab → Add OPENAI_API_KEY or OPENROUTER_API_KEY")
        sys.exit(1)
    
    logger.info("✅ Environment variables validated successfully")
    return telegram_token

# Validate environment before initializing bot
telegram_token = validate_environment()

# Initialize bot and dispatcher
bot = Bot(token=telegram_token)
dp = Dispatcher()

# Initialize fact generator and live location manager
fact_generator = UnifiedFactGenerator()
live_location_manager = LiveLocationManager(fact_generator, bot)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    await message.answer(
        "Привет! 👋 Я бот, который расскажет интересные факты о местах рядом с вами.\n\n"
        "🔹 **Статическая локация**: Отправьте геолокацию и получите интересный факт\n"
        "🔹 **Live Location**: Поделитесь live-локацией и получайте новые факты каждые 10 минут!\n\n"
        "📍 Чтобы отправить локацию, нажмите на скрепку и выберите 'Геопозиция'."
    )

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Handle /ping command for testing"""
    active_sessions = live_location_manager.get_active_sessions_count()
    await message.answer(f"Pong! 🏓 Бот работает!\nАктивных live-сессий: {active_sessions}")

@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    """Handle /stop command to stop live location tracking"""
    # Try to stop any active live sessions for this chat
    # Since we don't have message_id here, we'll need to iterate through sessions
    stopped_sessions = 0
    sessions_to_stop = []
    
    for session_key, session in live_location_manager.sessions.items():
        if session.chat_id == message.chat.id:
            sessions_to_stop.append((session.chat_id, session.message_id))
    
    for chat_id, message_id in sessions_to_stop:
        await live_location_manager.stop_live_session(chat_id, message_id)
        stopped_sessions += 1
    
    if stopped_sessions > 0:
        await message.answer(f"⏹️ Остановлено {stopped_sessions} активных сессий отслеживания.")
    else:
        await message.answer("Нет активных сессий для остановки.")

@dp.message(F.location)
async def handle_location(message: Message):
    """Handle location messages (both static and live)"""
    try:
        location = message.location
        latitude = location.latitude
        longitude = location.longitude
        live_period = location.live_period if hasattr(location, 'live_period') and location.live_period else None
        
        logger.info(f"Received location from user {message.from_user.id}: "
                   f"{latitude}, {longitude}, live_period: {live_period}")
        
        # Send "typing" action to show bot is working
        await bot.send_chat_action(message.chat.id, "typing")
        
        # Handle live location
        if live_period and live_period > 0:
            await live_location_manager.start_live_session(
                chat_id=message.chat.id,
                message_id=message.message_id,
                latitude=latitude,
                longitude=longitude,
                live_period=live_period
            )
        
        # Get and send fact for current location
        fact = await fact_generator.get_location_fact(latitude, longitude)
        
        location_type = "🔄 Live-локация" if live_period else "📍 Локация"
        await message.answer(f"{location_type} получена!\n\n🌍 Интересный факт о месте рядом с вами:\n\n{fact}")
        
    except Exception as e:
        logger.error(f"Error handling location: {e}")
        await message.answer(
            "Произошла ошибка при обработке вашей локации. Попробуйте ещё раз."
        )

@dp.edited_message(F.location)
async def handle_edited_location(message: Message):
    """Handle edited location messages (live location updates)"""
    try:
        location = message.location
        latitude = location.latitude
        longitude = location.longitude
        
        logger.info(f"Received location update from user {message.from_user.id}: "
                   f"{latitude}, {longitude}")
        
        # Update live location session
        await live_location_manager.update_live_session(
            chat_id=message.chat.id,
            message_id=message.message_id,
            latitude=latitude,
            longitude=longitude
        )
        
    except Exception as e:
        logger.error(f"Error handling edited location: {e}")

@dp.message()
async def handle_other_messages(message: Message):
    """Handle other messages"""
    await message.answer(
        "Я умею работать только с геолокацией! 📍\n\n"
        "Отправьте мне свою геолокацию, чтобы получить интересный факт о месте рядом с вами.\n\n"
        "Команды:\n"
        "/start - Начать работу\n"
        "/ping - Проверить статус\n"
        "/stop - Остановить отслеживание"
    )

async def periodic_cleanup():
    """Periodic cleanup of expired sessions"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            await live_location_manager.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

async def main():
    """Main function to start the bot"""
    logger.info("Starting Location Facts Bot v1.1...")
    
    # Start periodic cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        # Cancel cleanup task
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 