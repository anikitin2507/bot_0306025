import logging
import os
from openai_client import FactGenerator as OpenAIFactGenerator
from openrouter_client import OpenRouterFactGenerator

logger = logging.getLogger(__name__)

class UnifiedFactGenerator:
    """
    A unified client that tries OpenAI first and falls back to OpenRouter if OpenAI fails
    """
    def __init__(self):
        # Check if OpenAI key is available
        self.openai_available = bool(os.getenv('OPENAI_API_KEY'))
        
        # Check if OpenRouter key is available
        self.openrouter_available = bool(os.getenv('OPENROUTER_API_KEY'))
        
        # Initialize clients based on available keys
        self.openai_client = None
        self.openrouter_client = None
        
        if self.openai_available:
            try:
                self.openai_client = OpenAIFactGenerator()
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI client: {e}")
                self.openai_available = False
        
        if self.openrouter_available:
            try:
                self.openrouter_client = OpenRouterFactGenerator()
                logger.info("✅ OpenRouter client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenRouter client: {e}")
                self.openrouter_available = False
        
        if not self.openai_available and not self.openrouter_available:
            logger.error("❌ No AI services are available. Set either OPENAI_API_KEY or OPENROUTER_API_KEY.")
            raise ValueError("No AI services are available")
    
    async def get_location_fact(self, latitude: float, longitude: float) -> str:
        """
        Get a location fact using available AI services
        """
        # Try OpenAI first if available
        if self.openai_available and self.openai_client:
            try:
                logger.info("Trying to get fact using OpenAI...")
                fact = await self.openai_client.get_location_fact(latitude, longitude)
                
                # If we got a generic error message, consider it a failure and try OpenRouter
                if any(error_msg in fact for error_msg in [
                    "Извините, не удалось получить информацию",
                    "Извините, произошла ошибка",
                    "Извините, сервис временно"
                ]):
                    logger.warning("OpenAI returned an error message, trying OpenRouter...")
                    raise Exception("OpenAI returned error message")
                
                return fact
            except Exception as e:
                logger.warning(f"OpenAI request failed: {e}")
                
                # If OpenRouter is available, try it as fallback
                if self.openrouter_available and self.openrouter_client:
                    logger.info("Falling back to OpenRouter...")
                else:
                    return "Извините, не удалось получить информацию об этом месте. Сервис временно недоступен."
        
        # Use OpenRouter if OpenAI is not available or failed
        if self.openrouter_available and self.openrouter_client:
            try:
                logger.info("Getting fact using OpenRouter...")
                return await self.openrouter_client.get_location_fact(latitude, longitude)
            except Exception as e:
                logger.error(f"OpenRouter request also failed: {e}")
                return "Извините, не удалось получить информацию об этом месте. Все сервисы временно недоступны."
        
        # This point should only be reached if OpenAI wasn't available and was the only option
        return "Извините, не удалось получить информацию об этом месте. Сервис временно недоступен." 