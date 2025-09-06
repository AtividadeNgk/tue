from typing import Dict, Optional
from app.redis.client import redis_client
from app.database.crud import BotCRUD, InteractionCRUD
from app.bot.manager import BotManager
import json
import time

class WebhookHandler:
    @staticmethod
    async def process_webhook(bot_id: str, update: Dict) -> Dict:
        """Processar webhook do Telegram"""
        start_time = time.time()
        
        print(f"📥 Adicionando update à fila para bot {bot_id}")
        
        # Adicionar à fila para processamento assíncrono
        queue_data = {
            'bot_id': bot_id,
            'update': update,
            'timestamp': time.time()
        }
        
        # IMPORTANTE: Adicionar à fila
        await redis_client.add_to_queue('telegram_updates', queue_data)
        print(f"✅ Update adicionado à fila!")
        
        # Responder rapidamente (< 10ms)
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'status': 'queued',
            'processing_time_ms': processing_time
        }
    
    @staticmethod
    async def validate_secret_token(headers: Dict, bot_secret: str) -> bool:
        """Validar secret token do webhook"""
        telegram_secret = headers.get('X-Telegram-Bot-Api-Secret-Token')
        return telegram_secret == bot_secret
    
    @staticmethod
    async def extract_update_info(update: Dict) -> Dict:
        """Extrair informações relevantes do update"""
        info = {
            'type': None,
            'chat_id': None,
            'user_id': None,
            'username': None,
            'first_name': None,
            'text': None,
            'callback_data': None
        }
        
        # Mensagem normal
        if 'message' in update:
            message = update['message']
            info['type'] = 'message'
            info['chat_id'] = str(message['chat']['id'])
            info['user_id'] = str(message['from']['id'])
            info['username'] = message['from'].get('username')
            info['first_name'] = message['from'].get('first_name')
            info['text'] = message.get('text')
        
        # Callback query
        elif 'callback_query' in update:
            callback = update['callback_query']
            info['type'] = 'callback_query'
            info['chat_id'] = str(callback['message']['chat']['id'])
            info['user_id'] = str(callback['from']['id'])
            info['username'] = callback['from'].get('username')
            info['first_name'] = callback['from'].get('first_name')
            info['callback_data'] = callback.get('data')
            info['callback_id'] = callback.get('id')
        
        return info