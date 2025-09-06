from typing import Optional, Any
from app.redis.client import redis_client
import hashlib
import json

class CacheManager:
    @staticmethod
    def _generate_key(prefix: str, *args) -> str:
        """Gerar chave de cache"""
        key_parts = [str(arg) for arg in args]
        key_hash = hashlib.md5(''.join(key_parts).encode()).hexdigest()[:8]
        return f"{prefix}:{key_hash}"
    
    @staticmethod
    async def get_bot_config(bot_id: str) -> Optional[dict]:
        """Buscar configuração do bot do cache"""
        key = f"bot:config:{bot_id}"
        return await redis_client.get_cache(key)
    
    @staticmethod
    async def set_bot_config(bot_id: str, config: dict, ttl: int = 300) -> bool:
        """Salvar configuração do bot no cache"""
        key = f"bot:config:{bot_id}"
        return await redis_client.set_cache(key, config, ttl)
    
    @staticmethod
    async def invalidate_bot_config(bot_id: str) -> int:
        """Invalidar cache de configuração do bot"""
        pattern = f"bot:config:{bot_id}*"
        return await redis_client.delete_cache(pattern)
    
    @staticmethod
    async def get_user_state(bot_id: str, user_id: str) -> Optional[dict]:
        """Buscar estado do usuário"""
        key = f"user:state:{bot_id}:{user_id}"
        return await redis_client.get_cache(key)
    
    @staticmethod
    async def set_user_state(bot_id: str, user_id: str, state: dict) -> bool:
        """Salvar estado do usuário"""
        key = f"user:state:{bot_id}:{user_id}"
        return await redis_client.set_cache(key, state, ttl=3600)

cache_manager = CacheManager()