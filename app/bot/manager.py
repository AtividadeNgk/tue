from typing import Optional, List, Dict
from app.bot.telegram_api import telegram_api
from app.database.crud import BotCRUD
from app.redis.cache import cache_manager
from app.config import settings
import secrets
import hashlib

class BotManager:
    @staticmethod
    async def register_bot(db, token: str, user_id: int) -> Dict:
        """Registrar novo bot no sistema para o usuário"""
        # Validar token
        bot_info = await telegram_api.validate_token(token)
        if not bot_info:
            return {'success': False, 'error': 'Token inválido'}
        
        # Verificar se já existe
        existing_bot = await BotCRUD.get_bot_by_token(db, token)
        if existing_bot:
            # Verificar se é do mesmo usuário
            if existing_bot.user_id == user_id:
                return {'success': False, 'error': 'Você já cadastrou este bot'}
            else:
                return {'success': False, 'error': 'Este bot já está cadastrado por outro usuário'}
        
        # Gerar webhook secret
        webhook_secret = secrets.token_urlsafe(32)
        
        # MODO LOCAL: Não configurar webhook se for localhost
        webhook_active = False
        if 'localhost' not in settings.SERVER_URL and 'ngrok' in settings.SERVER_URL:
            webhook_url = f"{settings.SERVER_URL}{settings.WEBHOOK_PATH}/{bot_info['id']}"
            webhook_active = await telegram_api.set_webhook(token, webhook_url, webhook_secret)
        
        # Salvar no banco com user_id
        bot_data = {
            'token': token,
            'username': bot_info.get('username'),
            'bot_id': str(bot_info['id']),
            'webhook_secret': webhook_secret,
            'webhook_active': webhook_active
        }
        
        bot = await BotCRUD.create_bot(db, bot_data, user_id)
        
        return {
            'success': True,
            'bot': {
                'id': bot.bot_id,
                'username': bot.username,
                'created_at': str(bot.created_at),
                'mode': 'local' if not webhook_active else 'webhook'
            }
        }
    
    @staticmethod
    async def update_bot_config(db, bot_id: str, config: Dict) -> bool:
        """Atualizar configuração do bot"""
        await BotCRUD.update_bot(db, bot_id, config)
        await cache_manager.invalidate_bot_config(bot_id)
        return True
    
    @staticmethod
    async def get_bot_config(db, bot_id: str) -> Optional[Dict]:
        """Obter configuração do bot com cache"""
        cached = await cache_manager.get_bot_config(bot_id)
        if cached:
            return cached
        
        bot = await BotCRUD.get_bot_by_id(db, bot_id)
        if not bot:
            return None
        
        config = {
            'bot_id': bot.bot_id,
            'token': bot.token,
            'media_url': bot.media_url,
            'media_file_id': bot.media_file_id,
            'media_type': bot.media_type,
            'message_1': bot.message_1,
            'message_2': bot.message_2,
            'plans': bot.plans or []
        }
        
        await cache_manager.set_bot_config(bot_id, config)
        return config
    
    @staticmethod
    async def remove_bot(db, bot_id: str, user_id: int) -> bool:
        """Remover bot do sistema"""
        bot = await BotCRUD.get_bot_by_id(db, bot_id, user_id)
        if not bot:
            return False
        
        await telegram_api.delete_webhook(bot.token)
        await BotCRUD.delete_bot(db, bot_id, user_id)
        await cache_manager.invalidate_bot_config(bot_id)
        
        return True
    
    @staticmethod
    async def list_bots(db, user_id: int = None, active_only: bool = False) -> List[Dict]:
        """Listar bots (do usuário ou todos para admin)"""
        if user_id:
            bots = await BotCRUD.get_user_bots(db, user_id, active_only)
        else:
            bots = await BotCRUD.get_all_bots(db, active_only)
        
        return [{
            'id': bot.bot_id,
            'username': bot.username,
            'is_active': bot.is_active,
            'webhook_active': bot.webhook_active,
            'total_users': bot.total_users,
            'total_messages': bot.total_messages,
            'last_activity': str(bot.last_activity) if bot.last_activity else None,
            'created_at': str(bot.created_at)
        } for bot in bots]