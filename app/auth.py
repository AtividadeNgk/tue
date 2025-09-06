from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import User

# Configuração
SECRET_KEY = "sua-chave-secreta-123456"
ALGORITHM = "HS256"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    data = {"sub": email, "exp": expire}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        return email
    except:
        return None

async def get_current_user_optional(request, db: AsyncSession) -> Optional[User]:
    """Verificar se usuário está logado via cookie"""
    token = request.cookies.get("session")
    if not token:
        return None
    
    email = verify_token(token)
    if not email:
        return None
    
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()