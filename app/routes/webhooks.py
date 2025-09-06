from fastapi import APIRouter, Request, Response, Depends, HTTPException
from app.redis.cache import cache_manager
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.crud import BotCRUD
from app.bot.webhook import WebhookHandler
from app.bot.manager import BotManager
from app.bot.telegram_api import telegram_api
import time
import os
import asyncio

router = APIRouter(prefix="/webhook", tags=["webhooks"])

@router.post("/{bot_id}")
async def handle_webhook(
    bot_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Endpoint para receber webhooks do Telegram"""
    start_time = time.time()
    
    # Buscar bot
    bot = await BotCRUD.get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    
    # Processar update
    update = await request.json()
    print(f"📨 Webhook recebido para bot {bot_id}")
    
    # PROCESSAR DIRETO (SEM FILA) PARA TESTE LOCAL
    info = await WebhookHandler.extract_update_info(update)
    
    # Se for comando /start
    if info['type'] == 'message' and info['text'] == '/start':
        print(f"🚀 Processando /start de {info['username']}")
        
        # Buscar configuração
        config = await BotManager.get_bot_config(db, bot_id)
        
        if config:
            token = config['token']
            chat_id = info['chat_id']
            
            try:
                # 1. Enviar mídia (se configurada)
                if config.get('media_url') or config.get('media_file_id'):
                    print(f"📸 Enviando mídia...")
                    
                    if config.get('media_file_id'):
                        print(f"⚡ Usando file_id existente: {config['media_file_id'][:20]}...")
                        success = await telegram_api.send_media_by_file_id(
                            token, 
                            chat_id, 
                            config['media_file_id'],
                            config.get('media_type', 'photo')
                        )
                        if success:
                            print(f"✅ Mídia enviada via file_id (super rápido!)")
                    else:
                        print(f"📤 Primeira vez - obtendo file_id")
                        file_id = await telegram_api.send_media_and_get_file_id(
                            token,
                            chat_id,
                            config['media_url'],
                            config.get('media_type', 'photo')
                        )
                        
                        if file_id:
                            print(f"✅ File_id obtido: {file_id[:20]}...")
                            
                            # Salvar file_id no banco
                            await BotCRUD.update_bot(db, bot_id, {
                                'media_file_id': file_id,
                                'media_file_processed': True
                            })
                            
                            # Invalidar cache
                            await cache_manager.invalidate_bot_config(bot_id)
                            print(f"🔄 Cache invalidado para bot {bot_id}")
                            
                            # Deletar arquivo local se existir
                            if config.get('media_url'):
                                try:
                                    filename = config['media_url'].split('/')[-1].split('?')[0]
                                    filepath = f"static/uploads/{filename}"
                                    
                                    if os.path.exists(filepath):
                                        os.remove(filepath)
                                        print(f"🗑️ Arquivo local deletado: {filename}")
                                    else:
                                        print(f"📁 Arquivo não encontrado localmente: {filename}")
                                        
                                except Exception as e:
                                    print(f"⚠️ Não foi possível deletar arquivo: {e}")
                        else:
                            print(f"❌ Não foi possível obter file_id para a mídia")
                
                # 2. Preparar botões dos PLANOS (não mais "Ver Planos")
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
                
                # 3. Enviar mensagens com lógica dos botões de planos
                has_message_1 = config.get('message_1')
                has_message_2 = config.get('message_2')
                
                if has_message_1 and has_message_2:
                    # Tem as duas mensagens: envia mensagem 1 normal, mensagem 2 com botões dos planos
                    await telegram_api.send_message(token, chat_id, config['message_1'])
                    
                    if reply_markup:
                        await telegram_api.send_message(token, chat_id, config['message_2'], reply_markup)
                    else:
                        await telegram_api.send_message(token, chat_id, config['message_2'])
                        
                elif has_message_1:
                    # Só tem mensagem 1: envia com botões dos planos
                    if reply_markup:
                        await telegram_api.send_message(token, chat_id, config['message_1'], reply_markup)
                    else:
                        await telegram_api.send_message(token, chat_id, config['message_1'])
                        
                elif has_message_2:
                    # Só tem mensagem 2: envia com botões dos planos
                    if reply_markup:
                        await telegram_api.send_message(token, chat_id, config['message_2'], reply_markup)
                    else:
                        await telegram_api.send_message(token, chat_id, config['message_2'])
                
                elif reply_markup:
                    # Não tem texto mas tem planos: envia só os botões
                    await telegram_api.send_message(
                        token, 
                        chat_id, 
                        "📋 *Escolha seu plano:*", 
                        reply_markup
                    )
                
                # Se não tem texto nem planos: só mostra a mídia
                
            except Exception as e:
                print(f"❌ Erro ao enviar: {str(e)}")
                import traceback
                traceback.print_exc()
    
    # Se for callback de comprar plano
    elif info['type'] == 'callback_query' and info['callback_data'].startswith('buy_plan_'):
        print(f"💰 Processando seleção de plano")
        config = await BotManager.get_bot_config(db, bot_id)
        
        if config:
            token = config['token']
            plan_index = int(info['callback_data'].replace('buy_plan_', ''))
            plans = config.get('plans', [])
            
            if plan_index < len(plans):
                plan = plans[plan_index]
                
                if isinstance(plan, dict):
                    message = "✅ *Plano Selecionado:*\n\n"
                    message += f"📦 *Nome:* {plan.get('name')}\n"
                    message += f"💰 *Valor:* R$ {plan.get('value')}\n"
                    message += f"📅 *Duração:* {plan.get('days')} dias\n\n"
                    message += "_Para continuar, entre em contato com o suporte._"
                else:
                    message = f"✅ Você selecionou: {plan}"
                
                await telegram_api.answer_callback_query(
                    token,
                    info.get('callback_id'),
                    "Plano selecionado!",
                    show_alert=False
                )
                
                await telegram_api.send_message(token, info['chat_id'], message)
    
    # Responder rapidamente
    total_time = (time.time() - start_time) * 1000
    print(f"⏱️ Tempo de processamento: {total_time:.2f}ms")
    
    return Response(status_code=200)