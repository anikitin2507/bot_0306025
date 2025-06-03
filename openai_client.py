import os
import logging
import sys
from openai import OpenAI
from openai import RateLimitError, APIError
import asyncio
import time

logger = logging.getLogger(__name__)

class FactGenerator:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            logger.error("❌ OPENAI_API_KEY environment variable is not set!")
            logger.error("Please set OPENAI_API_KEY in your environment variables.")
            sys.exit(1)
        
        self.client = OpenAI(api_key=api_key)
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum 1 second between requests
        
        logger.info("✅ OpenAI client initialized successfully")
    
    async def _rate_limit(self):
        """Simple rate limiting to avoid hitting OpenAI limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def get_location_fact(self, latitude: float, longitude: float) -> str:
        """Get an interesting fact about a location using OpenAI GPT-4.1-mini"""
        try:
            await self._rate_limit()
            
            prompt = f"Ты экскурсовод. Дай 1 интересный факт о месте в пределах 1 км от координат {latitude}, {longitude}. Отвечай на русском языке, кратко и интересно."
            
            logger.info(f"Requesting fact for coordinates: {latitude}, {longitude}")
            
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",  # GPT-4.1-mini equivalent
                messages=[
                    {"role": "system", "content": "Ты знающий экскурсовод, который знает интересные факты о местах по всему миру. Отвечай кратко, но интересно."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,  # Reduced to save costs
                temperature=0.7,
                timeout=30  # 30 second timeout
            )
            
            fact = response.choices[0].message.content.strip()
            
            # Log token usage for monitoring
            if hasattr(response, 'usage'):
                usage = response.usage
                logger.info(f"OpenAI tokens used - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
            
            logger.info(f"Generated fact length: {len(fact)} characters")
            
            return fact
            
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            return "Извините, сервис временно перегружен. Попробуйте через несколько минут."
            
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return "Извините, произошла ошибка при получении информации. Попробуйте ещё раз."
            
        except Exception as e:
            logger.error(f"Unexpected error generating fact: {e}")
            return "Извините, не удалось получить информацию об этом месте. Попробуйте отправить локацию ещё раз." 