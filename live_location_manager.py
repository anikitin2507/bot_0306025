import asyncio
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

@dataclass
class LiveLocationSession:
    chat_id: int
    message_id: int
    latitude: float
    longitude: float
    live_period: int
    start_time: datetime
    last_update: datetime
    task: Optional[asyncio.Task] = None

class LiveLocationManager:
    def __init__(self, fact_generator, bot):
        self.fact_generator = fact_generator
        self.bot = bot
        self.sessions: Dict[str, LiveLocationSession] = {}
        self.update_interval = 600  # 10 minutes in seconds
    
    def _get_session_key(self, chat_id: int, message_id: int) -> str:
        """Generate unique session key"""
        return f"{chat_id}_{message_id}"
    
    async def start_live_session(self, chat_id: int, message_id: int, 
                                latitude: float, longitude: float, live_period: int):
        """Start a new live location session"""
        session_key = self._get_session_key(chat_id, message_id)
        
        # Stop existing session if any
        await self.stop_live_session(chat_id, message_id)
        
        # Create new session
        session = LiveLocationSession(
            chat_id=chat_id,
            message_id=message_id,
            latitude=latitude,
            longitude=longitude,
            live_period=live_period,
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        # Start periodic task
        session.task = asyncio.create_task(
            self._periodic_fact_sender(session)
        )
        
        self.sessions[session_key] = session
        
        logger.info(f"Started live location session for chat {chat_id}, "
                   f"message {message_id}, live_period: {live_period}s")
        
        # Send initial message
        await self.bot.send_message(
            chat_id,
            f"🔄 Начал отслеживание вашего местоположения!\n"
            f"Буду отправлять новые факты каждые 10 минут в течение {live_period // 60} минут."
        )
    
    async def update_live_session(self, chat_id: int, message_id: int, 
                                 latitude: float, longitude: float):
        """Update existing live location session with new coordinates"""
        session_key = self._get_session_key(chat_id, message_id)
        
        if session_key in self.sessions:
            session = self.sessions[session_key]
            session.latitude = latitude
            session.longitude = longitude
            session.last_update = datetime.now()
            
            logger.info(f"Updated live location session for chat {chat_id}: "
                       f"{latitude}, {longitude}")
        else:
            logger.warning(f"Attempted to update non-existent live session: {session_key}")
    
    async def stop_live_session(self, chat_id: int, message_id: int):
        """Stop live location session"""
        session_key = self._get_session_key(chat_id, message_id)
        
        if session_key in self.sessions:
            session = self.sessions[session_key]
            
            # Cancel the periodic task
            if session.task and not session.task.done():
                session.task.cancel()
                try:
                    await session.task
                except asyncio.CancelledError:
                    pass
            
            # Remove session
            del self.sessions[session_key]
            
            logger.info(f"Stopped live location session for chat {chat_id}")
            
            # Send stop message
            await self.bot.send_message(
                chat_id,
                "⏹️ Отслеживание местоположения завершено!"
            )
    
    async def _periodic_fact_sender(self, session: LiveLocationSession):
        """Periodically send facts for live location session"""
        try:
            # Wait for first interval
            await asyncio.sleep(self.update_interval)
            
            while True:
                # Check if session is still valid
                current_time = datetime.now()
                session_duration = (current_time - session.start_time).total_seconds()
                
                if session_duration >= session.live_period:
                    logger.info(f"Live session expired for chat {session.chat_id}")
                    break
                
                # Check if location was updated recently
                time_since_update = (current_time - session.last_update).total_seconds()
                if time_since_update > session.live_period:
                    logger.info(f"Live session stopped - no updates for chat {session.chat_id}")
                    break
                
                # Generate and send new fact
                try:
                    await self.bot.send_chat_action(session.chat_id, "typing")
                    
                    fact = await self.fact_generator.get_location_fact(
                        session.latitude, session.longitude
                    )
                    
                    await self.bot.send_message(
                        session.chat_id,
                        f"🌍 Новый факт о вашем текущем местоположении:\n\n{fact}"
                    )
                    
                    logger.info(f"Sent periodic fact to chat {session.chat_id}")
                    
                except Exception as e:
                    logger.error(f"Error sending periodic fact: {e}")
                
                # Wait for next interval
                await asyncio.sleep(self.update_interval)
                
        except asyncio.CancelledError:
            logger.info(f"Periodic fact sender cancelled for chat {session.chat_id}")
        except Exception as e:
            logger.error(f"Error in periodic fact sender: {e}")
        finally:
            # Clean up session
            session_key = self._get_session_key(session.chat_id, session.message_id)
            if session_key in self.sessions:
                del self.sessions[session_key]
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_key, session in self.sessions.items():
            session_duration = (current_time - session.start_time).total_seconds()
            if session_duration >= session.live_period:
                expired_sessions.append(session_key)
        
        for session_key in expired_sessions:
            session = self.sessions[session_key]
            await self.stop_live_session(session.chat_id, session.message_id)
    
    def get_active_sessions_count(self) -> int:
        """Get number of active live sessions"""
        return len(self.sessions) 