from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.webhook import WebhookHandler
from app.bot.manager import BotManager
from app.bot.telegram_api import telegram_api
from app.database.crud import BotCRUD, InteractionCRUD
from app.utils.rate_limiter import rate_limiter
from app.redis.cache import cache_manager
import json
import asyncio

class MessageProcessor:
    async def process_update(self, db: AsyncSession, bot_id: str, update: Dict):
        """Processar update do Telegram"""
        try:
            print(f"🔍 Processando update para bot {bot_id}")
            
            # Verificar rate limit
            if not await rate_limiter.is_allowed(bot_id):
                print(f"⚠️ Rate limit excedido para bot {bot_id}")
                return
            
            # Extrair informações do update
            info = await WebhookHandler.extract_update_info(update)
            
            if not info['type']:
                return
            
            print(f"📝 Tipo: {info['type']}, Comando: {info.get('text')}")
            
            # Registrar interação
            await self._register_interaction(db, bot_id, info)
            
            # Processar comando /start
            if info['type'] == 'message' and info['text'] == '/start':
                print(f"🚀 Processando comando /start")
                await self._handle_start_command(db, bot_id, info['chat_id'])
            
            # Processar callback de planos
            elif info['type'] == 'callback_query' and info['callback_data'] == 'view_plans':
                print(f"📋 Processando callback de planos")
                await self._handle_plans_callback(db, bot_id, info)
            
            # Incrementar estatísticas
            await BotCRUD.increment_stats(db, bot_id, 'total_messages')
            
            print(f"✅ Update processado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao processar update: {str(e)}")
            import traceback
            traceback.print_exc()
            await BotCRUD.update_bot(db, bot_id, {'last_error': str(e)})
    
    async def _register_interaction(self, db: AsyncSession, bot_id: str, info: Dict):
        """Registrar interação do usuário"""
        interaction_data = {
            'bot_id': bot_id,
            'user_id': info['user_id'],
            'username': info.get('username'),
            'first_name': info.get('first_name'),
            'command': info['text'] if info.get('text', '').startswith('/') else None,
            'callback_data': info.get('callback_data'),
            'message_text': info.get('text')
        }
        
        await InteractionCRUD.create_interaction(db, interaction_data)
        print(f"📊 Interação registrada: {info['username']} - {info.get('text')}")
    
    async def _handle_start_command(self, db: AsyncSession, bot_id: str, chat_id: str):
        """Processar comando /start"""
        print(f"💬 Enviando resposta para chat_id: {chat_id}")
        
        # Buscar configuração do bot (com cache)
        config = await BotManager.get_bot_config(db, bot_id)
        
        if not config:
            print(f"⚠️ Configuração não encontrada para bot {bot_id}")
            return
        
        token = config['token']
        
        try:
            # 1. Enviar mídia (se configurada)
            if config.get('media_url'):
                print(f"📸 Enviando mídia: {config['media_url']}")
                if config.get('media_type') == 'video':
                    await telegram_api.send_video(token, chat_id, config['media_url'])
                else:
                    await telegram_api.send_photo(token, chat_id, config['media_url'])
                
                await asyncio.sleep(0.5)
            
            # 2. Preparar botões dos PLANOS
            plans = config.get('plans', [])
            reply_markup = None
            
            if plans and len(plans) > 0:
                keyboard = []
                
                for i, plan in enumerate(plans):
                    if isinstance(plan, dict):
                        plan_text = f"💎 {plan.get('name', 'Plano')} - R$ {plan.get('value', '0')} ({plan.get('days', '30')} dias)"
                    else:
                        plan_text = str(plan)
                    
                    keyboard.append([{
                        'text': plan_text,
                        'callback_data': f'buy_plan_{i}'
                    }])
                
                reply_markup = {'inline_keyboard': keyboard}
            
            # 3. Enviar mensagens com botões dos planos
            has_message_1 = config.get('message_1')
            has_message_2 = config.get('message_2')
            
            if has_message_1 and has_message_2:
                print(f"💬 Enviando mensagem 1")
                await telegram_api.send_message(token, chat_id, config['message_1'])
                await asyncio.sleep(0.5)
                
                if reply_markup:
                    print(f"💬 Enviando mensagem 2 com planos")
                    await telegram_api.send_message(token, chat_id, config['message_2'], reply_markup)
                else:
                    print(f"💬 Enviando mensagem 2")
                    await telegram_api.send_message(token, chat_id, config['message_2'])
                
            elif has_message_1:
                if reply_markup:
                    print(f"💬 Enviando mensagem 1 com planos")
                    await telegram_api.send_message(token, chat_id, config['message_1'], reply_markup)
                else:
                    print(f"💬 Enviando mensagem 1")
                    await telegram_api.send_message(token, chat_id, config['message_1'])
                
            elif has_message_2:
                if reply_markup:
                    print(f"💬 Enviando mensagem 2 com planos")
                    await telegram_api.send_message(token, chat_id, config['message_2'], reply_markup)
                else:
                    print(f"💬 Enviando mensagem 2")
                    await telegram_api.send_message(token, chat_id, config['message_2'])
                    
            elif reply_markup:
                # Sem texto mas com planos
                print(f"💎 Enviando apenas planos")
                await telegram_api.send_message(token, chat_id, "📋 *Escolha seu plano:*", reply_markup)
            else:
                print(f"📸 Apenas mídia enviada")
            
            print(f"✅ Comando /start processado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagens: {str(e)}")
            raise
    
    async def _handle_plans_callback(self, db: AsyncSession, bot_id: str, info: Dict):
        """Processar callback de visualizar planos"""
        # Buscar configuração
        config = await BotManager.get_bot_config(db, bot_id)
        
        if not config:
            return
        
        token = config['token']
        plans = config.get('plans', [])
        
        # Responder callback
        if plans:
            plans_text = "📋 *Planos disponíveis:*\n\n"
            for i, plan in enumerate(plans, 1):
                plans_text += f"{i}. {plan}\n"
        else:
            plans_text = "Nenhum plano configurado ainda."
        
        await telegram_api.answer_callback_query(
            token,
            info['callback_id'],
            plans_text,
            show_alert=True
        )
        print(f"📋 Callback de planos respondido")