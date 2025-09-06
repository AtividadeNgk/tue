from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime
from app.database.models import Bot, UserInteraction, BotStatistics, User

class BotCRUD:
    @staticmethod
    async def create_bot(db: AsyncSession, bot_data: dict, user_id: int) -> Bot:
        """Criar novo bot para o usuário"""
        bot = Bot(**bot_data, user_id=user_id)
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        return bot
    
    @staticmethod
    async def get_bot_by_id(db: AsyncSession, bot_id: str, user_id: Optional[int] = None) -> Optional[Bot]:
        """Buscar bot por ID (opcionalmente filtrado por usuário)"""
        query = select(Bot).where(Bot.bot_id == bot_id)
        if user_id:
            query = query.where(Bot.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_bot_by_token(db: AsyncSession, token: str) -> Optional[Bot]:
        """Buscar bot por token (para webhook, não precisa user_id)"""
        result = await db.execute(
            select(Bot).where(Bot.token == token)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_bots(db: AsyncSession, user_id: int, active_only: bool = False) -> List[Bot]:
        """Listar bots do usuário específico"""
        query = select(Bot).where(Bot.user_id == user_id)
        if active_only:
            query = query.where(Bot.is_active == True)
        query = query.order_by(Bot.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_all_bots(db: AsyncSession, active_only: bool = False) -> List[Bot]:
        """Listar todos os bots (para admin)"""
        query = select(Bot)
        if active_only:
            query = query.where(Bot.is_active == True)
        query = query.order_by(Bot.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_bot(db: AsyncSession, bot_id: str, bot_data: dict, user_id: Optional[int] = None) -> Optional[Bot]:
        """Atualizar bot (opcionalmente verificando ownership)"""
        bot_data['updated_at'] = datetime.utcnow()
        
        query = update(Bot).where(Bot.bot_id == bot_id)
        if user_id:
            query = query.where(Bot.user_id == user_id)
        
        await db.execute(query.values(**bot_data))
        await db.commit()
        
        return await BotCRUD.get_bot_by_id(db, bot_id, user_id)
    
    @staticmethod
    async def delete_bot(db: AsyncSession, bot_id: str, user_id: Optional[int] = None) -> bool:
        """Deletar bot (opcionalmente verificando ownership)"""
        query = delete(Bot).where(Bot.bot_id == bot_id)
        if user_id:
            query = query.where(Bot.user_id == user_id)
        
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def increment_stats(db: AsyncSession, bot_id: str, field: str = 'total_messages'):
        """Incrementar estatísticas do bot"""
        await db.execute(
            update(Bot)
            .where(Bot.bot_id == bot_id)
            .values({
                field: Bot.__table__.c[field] + 1,
                'last_activity': datetime.utcnow()
            })
        )
        await db.commit()
    
    @staticmethod
    async def count_user_bots(db: AsyncSession, user_id: int) -> int:
        """Contar quantos bots o usuário tem"""
        result = await db.execute(
            select(func.count(Bot.id)).where(Bot.user_id == user_id)
        )
        return result.scalar() or 0

class InteractionCRUD:
    @staticmethod
    async def create_interaction(db: AsyncSession, interaction_data: dict) -> UserInteraction:
        """Registrar interação do usuário"""
        interaction = UserInteraction(**interaction_data)
        db.add(interaction)
        await db.commit()
        return interaction
    
    @staticmethod
    async def get_bot_interactions(db: AsyncSession, bot_id: str, limit: int = 100):
        """Buscar interações de um bot"""
        result = await db.execute(
            select(UserInteraction)
            .where(UserInteraction.bot_id == bot_id)
            .order_by(UserInteraction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def count_unique_users(db: AsyncSession, bot_id: str) -> int:
        """Contar usuários únicos"""
        result = await db.execute(
            select(func.count(func.distinct(UserInteraction.user_id)))
            .where(UserInteraction.bot_id == bot_id)
        )
        return result.scalar() or 0

class UserCRUD:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Buscar usuário por email"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: dict) -> User:
        """Criar novo usuário"""
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user