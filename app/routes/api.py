from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
from app.database.connection import get_db
from app.bot.manager import BotManager
from app.database.crud import BotCRUD, InteractionCRUD
from app.auth import get_current_user_optional
from app.config import settings
import os
import shutil
import uuid

router = APIRouter(prefix="/api", tags=["api"])

# Criar pasta de uploads se não existir
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Schemas
class BotCreate(BaseModel):
    token: str

class BotConfig(BaseModel):
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    message_1: Optional[str] = None
    message_2: Optional[str] = None
    plans: Optional[Any] = []

class BotResponse(BaseModel):
    id: str
    username: str
    is_active: bool
    total_users: int
    total_messages: int

# Rotas
@router.post("/bots")
async def create_bot(
    bot_data: BotCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Criar novo bot"""
    # Verificar autenticação
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    try:
        print(f"📝 Usuário {user.email} criando bot...")
        
        # REMOVIDO: Verificação de limite
        
        result = await BotManager.register_bot(db, bot_data.token, user.id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        print(f"✅ Bot criado para usuário {user.email}")
        return result
    except Exception as e:
        print(f"💥 Erro ao criar bot: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/bots")
async def list_bots(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Listar bots do usuário logado"""
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    # Buscar apenas bots do usuário
    bots = await BotCRUD.get_user_bots(db, user.id)
    
    # Formatar resposta
    bots_list = []
    for bot in bots:
        unique_users = await InteractionCRUD.count_unique_users(db, bot.bot_id)
        bots_list.append({
            'id': bot.bot_id,
            'username': bot.username,
            'is_active': bot.is_active,
            'webhook_active': bot.webhook_active,
            'total_users': unique_users,
            'total_messages': bot.total_messages,
            'last_activity': str(bot.last_activity) if bot.last_activity else None,
            'created_at': str(bot.created_at)
        })
    
    return {'bots': bots_list}

@router.get("/bots/{bot_id}")
async def get_bot(
    bot_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Obter detalhes do bot"""
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    # Buscar bot verificando ownership
    bot = await BotCRUD.get_bot_by_id(db, bot_id, user.id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    
    # Buscar estatísticas
    unique_users = await InteractionCRUD.count_unique_users(db, bot_id)
    
    return {
        'id': bot.bot_id,
        'username': bot.username,
        'is_active': bot.is_active,
        'webhook_active': bot.webhook_active,
        'config': {
            'media_url': bot.media_url,
            'media_type': bot.media_type,
            'media_file_id': bot.media_file_id,
            'message_1': bot.message_1,
            'message_2': bot.message_2,
            'plans': bot.plans or []
        },
        'stats': {
            'total_users': unique_users,
            'total_messages': bot.total_messages,
            'messages_today': bot.messages_today,
            'last_activity': str(bot.last_activity) if bot.last_activity else None
        },
        'created_at': str(bot.created_at)
    }

@router.put("/bots/{bot_id}/config")
async def update_bot_config(
    bot_id: str,
    config: BotConfig,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Atualizar configuração do bot"""
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    # Verificar ownership
    bot = await BotCRUD.get_bot_by_id(db, bot_id, user.id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    
    config_dict = config.dict()
    
    # Detectar tipo de mídia automaticamente
    if config_dict.get('media_url'):
        url = config_dict['media_url'].lower()
        if any(ext in url for ext in ['.mp4', '.avi', '.mov', '.webm']):
            config_dict['media_type'] = 'video'
        elif any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            config_dict['media_type'] = 'photo'
        elif not config_dict.get('media_type'):
            config_dict['media_type'] = 'photo'
    
    # Limpar file_id se mídia mudou
    if config_dict.get('media_url') and config_dict.get('media_url') != bot.media_url:
        config_dict['media_file_id'] = None
        config_dict['media_file_processed'] = False
    
    # Atualizar com verificação de ownership
    success = await BotCRUD.update_bot(db, bot_id, config_dict, user.id)
    
    # Limpar cache
    from app.redis.cache import cache_manager
    await cache_manager.invalidate_bot_config(bot_id)
    
    return {'success': bool(success)}

@router.delete("/bots/{bot_id}")
async def delete_bot(
    bot_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Deletar bot"""
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    # Deletar com verificação de ownership
    success = await BotManager.remove_bot(db, bot_id, user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    
    return {'success': True}

@router.get("/bots/{bot_id}/stats")
async def get_bot_stats(
    bot_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Obter estatísticas do bot"""
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    # Verificar ownership
    bot = await BotCRUD.get_bot_by_id(db, bot_id, user.id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    
    interactions = await InteractionCRUD.get_bot_interactions(db, bot_id, limit=50)
    unique_users = await InteractionCRUD.count_unique_users(db, bot_id)
    
    return {
        'total_users': unique_users,
        'total_messages': bot.total_messages,
        'messages_today': bot.messages_today,
        'recent_interactions': [
            {
                'user_id': i.user_id,
                'username': i.username,
                'command': i.command,
                'created_at': str(i.created_at)
            }
            for i in interactions
        ]
    }

@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)  # ← ADICIONAR DB
):
    """Upload de arquivo de mídia"""
    # Verificar autenticação
    user = await get_current_user_optional(request, db)  # ← PASSAR DB CORRETO
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    # Validar tamanho (10MB)
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Arquivo muito grande (máx 10MB)")
    
    # Detectar tipo
    media_type = "photo"
    if file.content_type:
        if file.content_type.startswith('video/'):
            media_type = "video"
        elif not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Tipo de arquivo inválido")
    
    # Gerar nome único com user_id para evitar conflitos
    extension = file.filename.split('.')[-1]
    filename = f"user_{user.id}_{uuid.uuid4()}.{extension}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Salvar arquivo
    with open(filepath, "wb") as buffer:
        buffer.write(contents)
    
    # Retornar URL
    server_url = settings.SERVER_URL
    if 'localhost' in server_url:
        url = f"http://localhost:8000/static/uploads/{filename}"
    else:
        url = f"{server_url}/static/uploads/{filename}"
    
    return {
        "success": True,
        "url": url,
        "filename": filename,
        "type": media_type
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'telegram-bot-manager',
        'version': '1.0.0'
    }

@router.get("/user/stats")
async def get_user_stats(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Estatísticas do usuário"""
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    bot_count = await BotCRUD.count_user_bots(db, user.id)
    bots = await BotCRUD.get_user_bots(db, user.id)
    
    total_messages = sum(bot.total_messages for bot in bots)
    total_users = sum(bot.total_users for bot in bots)
    
    return {
        'email': user.email,
        'bot_count': bot_count,
        'bot_limit': 10,
        'total_messages': total_messages,
        'total_users': total_users,
        'member_since': str(user.created_at)
    }