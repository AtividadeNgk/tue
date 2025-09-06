import aiohttp
import asyncio
from typing import Optional, Dict, Any
from app.config import settings
import hashlib
import secrets

class TelegramAPI:
    def __init__(self):
        self.base_url = settings.TELEGRAM_API_URL
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Obter ou criar sessão HTTP"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=settings.HTTP_POOL_SIZE,
                ttl_dns_cache=300
            )
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self.session
    
    async def make_request(self, token: str, method: str, data: Dict[str, Any] = None) -> Dict:
        """Fazer requisição à API do Telegram"""
        url = f"{self.base_url}/bot{token}/{method}"
        session = await self.get_session()
        
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                if not result.get('ok'):
                    raise Exception(f"Telegram API Error: {result.get('description')}")
                return result.get('result', {})
        except asyncio.TimeoutError:
            raise Exception("Timeout ao conectar com Telegram API")
        except Exception as e:
            raise Exception(f"Erro na requisição: {str(e)}")
    
    async def validate_token(self, token: str) -> Optional[Dict]:
        """Validar token e obter informações do bot"""
        try:
            bot_info = await self.make_request(token, 'getMe')
            return bot_info
        except:
            return None
    
    async def set_webhook(self, token: str, webhook_url: str, secret_token: str = None) -> bool:
        """Configurar webhook do bot"""
        secret_token = secret_token or secrets.token_urlsafe(32)
        
        data = {
            'url': webhook_url,
            'secret_token': secret_token,
            'allowed_updates': ['message', 'callback_query'],
            'drop_pending_updates': True,
            'max_connections': 100
        }
        
        try:
            result = await self.make_request(token, 'setWebhook', data)
            return result == True
        except:
            return False
    
    async def delete_webhook(self, token: str) -> bool:
        """Remover webhook do bot"""
        try:
            result = await self.make_request(token, 'deleteWebhook')
            return result == True
        except:
            return False
    
    async def send_message(self, token: str, chat_id: str, text: str, 
                        reply_markup: Dict = None) -> Optional[Dict]:
        """Enviar mensagem"""
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        if reply_markup:
            data['reply_markup'] = reply_markup
        
        try:
            result = await self.make_request(token, 'sendMessage', data)
            return result
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {str(e)}")
            return None
    
    async def send_photo(self, token: str, chat_id: str, photo_url: str) -> Optional[Dict]:
        """Enviar foto"""
        data = {
            'chat_id': chat_id,
            'photo': photo_url
        }
        
        try:
            return await self.make_request(token, 'sendPhoto', data)
        except:
            return None
    
    async def send_video(self, token: str, chat_id: str, video_url: str) -> Optional[Dict]:
        """Enviar vídeo"""
        data = {
            'chat_id': chat_id,
            'video': video_url
        }
        
        print(f"🎥 Enviando vídeo: {video_url}")  # Debug
        
        try:
            result = await self.make_request(token, 'sendVideo', data)
            print(f"📹 Resposta do Telegram: {result}")  # Debug
            return result
        except Exception as e:
            print(f"❌ Erro ao enviar vídeo: {str(e)}")  # Debug
            return None
        
    async def send_media_and_get_file_id(self, token: str, chat_id: str, media_url: str, media_type: str = 'photo') -> Optional[str]:
        """Enviar mídia e retornar file_id"""
        try:
            print(f"📤 Tentando enviar {media_type}: {media_url}")
            
            if media_type == 'video':
                result = await self.send_video(token, chat_id, media_url)
                print(f"📹 Resultado do vídeo: {result}")
                
                if result:
                    if 'video' in result:
                        file_id = result['video']['file_id']
                        print(f"✅ File_id do vídeo obtido: {file_id[:30]}...")
                        return file_id
                    else:
                        print(f"⚠️ Resposta não contém 'video': {result}")
            else:
                result = await self.send_photo(token, chat_id, media_url)
                print(f"📸 Resultado da foto: {result}")
                
                if result:
                    if 'photo' in result:
                        file_id = result['photo'][-1]['file_id']
                        print(f"✅ File_id da foto obtido: {file_id[:30]}...")
                        return file_id
                    else:
                        print(f"⚠️ Resposta não contém 'photo': {result}")
            
            print(f"❌ Não foi possível obter file_id")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao obter file_id: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def send_media_by_file_id(self, token: str, chat_id: str, file_id: str, media_type: str = 'photo') -> bool:
        """Enviar mídia usando file_id (muito mais rápido)"""
        try:
            if media_type == 'video':
                data = {'chat_id': chat_id, 'video': file_id}
                await self.make_request(token, 'sendVideo', data)
            else:
                data = {'chat_id': chat_id, 'photo': file_id}
                await self.make_request(token, 'sendPhoto', data)
            return True
        except:
            return False
    
    async def answer_callback_query(self, token: str, callback_query_id: str, 
                                   text: str = None, show_alert: bool = False) -> bool:
        """Responder callback query"""
        data = {
            'callback_query_id': callback_query_id,
            'text': text,
            'show_alert': show_alert
        }
        
        try:
            await self.make_request(token, 'answerCallbackQuery', data)
            return True
        except:
            return False
    
    async def close(self):
        """Fechar sessão HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()

telegram_api = TelegramAPI()