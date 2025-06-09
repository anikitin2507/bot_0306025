import os
import logging
import sys
import asyncio
import time
import aiohttp

logger = logging.getLogger(__name__)

class OpenRouterFactGenerator:
    def __init__(self):
        api_key = os.getenv('OPENROUTER_API_KEY')
        
        if not api_key:
            logger.error("❌ OPENROUTER_API_KEY environment variable is not set!")
            logger.error("Please set OPENROUTER_API_KEY in your environment variables.")
            sys.exit(1)
        
        self.api_key = api_key
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum 1 second between requests
        
        logger.info("✅ OpenRouter client initialized successfully")
    
    async def _rate_limit(self):
        """Simple rate limiting to avoid hitting API limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def get_location_fact(self, latitude: float, longitude: float) -> str:
        """Get an interesting fact about a location using OpenRouter API with GPT-4-Turbo"""
        try:
            await self._rate_limit()
            
            prompt = f"Ты экскурсовод. Дай 1 интересный факт о месте в пределах 1 км от координат {latitude}, {longitude}. Отвечай на русском языке, кратко и интересно."
            
            logger.info(f"Requesting fact via OpenRouter for coordinates: {latitude}, {longitude}")
            
            # OpenRouter endpoint
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            # Request headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://your-site-url.com",  # Update with your site
                "X-Title": "Location Facts Bot"  # Your app name
            }
            
            # Request body
            data = {
                "model": "anthropic/claude-3-haiku",  # You can also use "openai/gpt-4-turbo" or other models
                "messages": [
                    {"role": "system", "content": "Ты знающий экскурсовод, который знает интересные факты о местах по всему миру. Отвечай кратко, но интересно."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                        return "Извините, произошла ошибка при получении информации. Попробуйте ещё раз."
                    
                    response_data = await response.json()
                    
                    fact = response_data["choices"][0]["message"]["content"].strip()
                    
                    if "usage" in response_data:
                        usage = response_data["usage"]
                        logger.info(f"OpenRouter tokens used - Prompt: {usage.get('prompt_tokens', 0)}, "
                                    f"Completion: {usage.get('completion_tokens', 0)}, "
                                    f"Total: {usage.get('total_tokens', 0)}")
                    
                    logger.info(f"Generated fact length: {len(fact)} characters")
                    
                    return fact
            
        except asyncio.TimeoutError:
            logger.error("OpenRouter API request timed out")
            return "Извините, сервис временно недоступен. Попробуйте через несколько минут."
            
        except Exception as e:
            logger.error(f"Unexpected error generating fact via OpenRouter: {e}")
            return "Извините, не удалось получить информацию об этом месте. Попробуйте отправить локацию ещё раз." 