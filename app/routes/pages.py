from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.database.models import User
from app.database.crud import BotCRUD
from app.auth import verify_token

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")

async def get_current_user(request: Request, db: AsyncSession):
    """Verificar se usuário está logado"""
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

@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Página principal - Dashboard"""
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Buscar apenas bots do usuário
    bots = await BotCRUD.get_user_bots(db, user.id)
    
    # Formatar para template
    bots_list = []
    for bot in bots:
        bots_list.append({
            'id': bot.bot_id,
            'username': bot.username or 'Bot sem nome',
            'is_active': bot.is_active,
            'total_users': bot.total_users,
            'total_messages': bot.total_messages
        })
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "page": "dashboard",
            "bots": bots_list,
            "total_bots": len(bots_list),
            "active_bots": len([b for b in bots_list if b['is_active']])
        }
    )

@router.get("/bots", response_class=HTMLResponse)
async def bots_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Página de gerenciamento de bots"""
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    bots = await BotCRUD.get_user_bots(db, user.id)
    
    bots_list = []
    for bot in bots:
        bots_list.append({
            'id': bot.bot_id,
            'username': bot.username or 'Bot sem nome',
            'is_active': bot.is_active,
            'total_users': bot.total_users,
            'total_messages': bot.total_messages
        })
    
    return templates.TemplateResponse(
        "pages/bots.html",
        {
            "request": request,
            "page": "bots",
            "bots": bots_list,
            "user_email": user.email
        }
    )

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Página de configurações"""
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    bot_count = await BotCRUD.count_user_bots(db, user.id)
    
    return templates.TemplateResponse(
        "pages/settings.html",
        {
            "request": request,
            "page": "settings",
            "user_email": user.email,
            "bot_count": bot_count,
            "bot_limit": 10,
            "member_since": user.created_at
        }
    )