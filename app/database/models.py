from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Para admin geral
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamento
    bots = relationship("Bot", back_populates="owner", cascade="all, delete-orphan")

class Bot(Base):
    __tablename__ = 'bots'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(100))
    bot_id = Column(String(50), unique=True, index=True)
    webhook_secret = Column(String(64))
    
    # Configurações de mensagens
    media_url = Column(Text)
    media_type = Column(String(20), default='photo')
    media_file_id = Column(Text)
    media_file_processed = Column(Boolean, default=False)
    message_1 = Column(Text)
    message_2 = Column(Text)
    plans = Column(JSON, default=list)
    
    # Estatísticas
    total_users = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    messages_today = Column(Integer, default=0)
    last_activity = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    webhook_active = Column(Boolean, default=False)
    last_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamento
    owner = relationship("User", back_populates="bots")
    
    # Índices otimizados
    __table_args__ = (
        Index('idx_user_bots', 'user_id', 'created_at'),
        Index('idx_user_active', 'user_id', 'is_active'),
        Index('idx_bot_webhook', 'bot_id', 'webhook_active'),
    )

class UserInteraction(Base):
    __tablename__ = 'user_interactions'
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(String(50), index=True)
    user_id = Column(String(50), index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    command = Column(String(50))
    callback_data = Column(String(200))
    message_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_bot_interactions', 'bot_id', 'created_at'),
        Index('idx_user_interactions', 'user_id', 'created_at'),
    )

class BotStatistics(Base):
    __tablename__ = 'bot_statistics'
    
    id = Column(Integer, primary_key=True)
    bot_id = Column(String(50), index=True)
    date = Column(DateTime(timezone=True), index=True)
    messages_sent = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    avg_response_time = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())