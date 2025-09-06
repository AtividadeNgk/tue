from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.database.models import User
from app.auth import verify_password, get_password_hash, create_access_token as create_token
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Página de cadastro"""
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Processar login"""
    # Buscar usuário
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    # Verificar senha
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Email ou senha incorretos"}
        )
    
    # Criar token
    token = create_token(user.email)
    
    # Redirecionar com cookie
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session",
        value=token,
        max_age=604800,  # 7 dias
        httponly=True
    )
    return response

@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Processar cadastro"""
    # Validar senhas
    if password != password_confirm:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "As senhas não coincidem"}
        )
    
    if len(password) < 6:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "A senha deve ter pelo menos 6 caracteres"}
        )
    
    # Verificar se email já existe
    result = await db.execute(
        select(User).where(User.email == email)
    )
    if result.scalar_one_or_none():
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Email já cadastrado"}
        )
    
    # Criar usuário
    user = User(
        email=email,
        hashed_password=get_password_hash(password)
    )
    db.add(user)
    await db.commit()
    
    # Fazer login automático
    token = create_token(email)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session",
        value=token,
        max_age=604800,
        httponly=True
    )
    return response

@router.get("/logout")
async def logout():
    """Fazer logout"""
    response = RedirectResponse(url="/login")
    response.delete_cookie("session")
    return response