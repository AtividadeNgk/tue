import json
from typing import Optional, Any
from app.config import settings

class RedisClient:
    """Versão simplificada do Redis para teste local"""
    _instance = None
    _cache = {}
    _queue = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """Simular conexão"""
        return self
    
    async def get_client(self):
        """Obter cliente"""
        return self
    
    async def add_to_queue(self, queue_name: str, data: dict) -> int:
        """Adicionar item à fila simulada"""
        if queue_name not in self._queue:
            self._queue[queue_name] = []
        self._queue[queue_name].append(json.dumps(data))
        return len(self._queue[queue_name])
    
    async def get_from_queue(self, queue_name: str, timeout: int = 1) -> Optional[dict]:
        """Pegar item da fila simulada"""
        if queue_name in self._queue and self._queue[queue_name]:
            data = self._queue[queue_name].pop(0)
            return json.loads(data)
        return None
    
    async def set_cache(self, key: str, value: Any, ttl: int = None) -> bool:
        """Salvar no cache simulado"""
        self._cache[key] = json.dumps(value)
        return True
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Buscar do cache simulado"""
        if key in self._cache:
            return json.loads(self._cache[key])
        return None
    
    async def delete_cache(self, pattern: str) -> int:
        """Deletar cache por padrão"""
        count = 0
        keys_to_delete = []
        for key in self._cache:
            if pattern.replace('*', '') in key:
                keys_to_delete.append(key)
                count += 1
        for key in keys_to_delete:
            del self._cache[key]
        return count
    
    async def increment_rate_limit(self, key: str, window: int = 1) -> int:
        """Incrementar contador de rate limit simulado"""
        if key not in self._cache:
            self._cache[key] = "0"
        current = int(self._cache[key])
        current += 1
        self._cache[key] = str(current)
        return current
    
    async def get_rate_limit(self, key: str) -> int:
        """Verificar rate limit atual"""
        if key in self._cache:
            return int(self._cache[key])
        return 0

redis_client = RedisClient()