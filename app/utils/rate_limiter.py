from app.redis.client import redis_client
from app.config import settings

class RateLimiter:
    @staticmethod
    async def check_limit(bot_id: str) -> bool:
        """Verificar se bot está dentro do rate limit"""
        key = f"rate_limit:{bot_id}"
        current = await redis_client.get_rate_limit(key)
        return current < settings.RATE_LIMIT_PER_BOT
    
    @staticmethod
    async def increment(bot_id: str) -> int:
        """Incrementar contador de rate limit"""
        key = f"rate_limit:{bot_id}"
        return await redis_client.increment_rate_limit(key, window=1)
    
    @staticmethod
    async def is_allowed(bot_id: str) -> bool:
        """Verificar e incrementar se permitido"""
        if await RateLimiter.check_limit(bot_id):
            await RateLimiter.increment(bot_id)
            return True
        return False

rate_limiter = RateLimiter()