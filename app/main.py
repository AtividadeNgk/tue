from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

# Importar rotas
from app.routes import api, webhooks, pages, auth
from app.bot.telegram_api import telegram_api
from app.redis.client import redis_client

# Lifespan para gerenciar conexões
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Iniciando sistema...")
    
    # Criar tabelas automaticamente
    from app.database.connection import init_db
    try:
        init_db()
        print("✅ Banco de dados verificado/criado")
    except Exception as e:
        print(f"⚠️ Aviso no banco: {str(e)}")
    
    # Conectar Redis
    await redis_client.connect()
    print("✅ Redis conectado")
    
    yield
    
    # Shutdown
    print("🔄 Encerrando sistema...")
    await telegram_api.close()
    print("✅ Sistema encerrado")

# Criar app
app = FastAPI(
    title="Telegram Bot Manager",
    version="1.0.0",
    lifespan=lifespan
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir rotas de autenticação PRIMEIRO
app.include_router(auth.router)

# Incluir outras rotas
app.include_router(api.router)
app.include_router(webhooks.router)
app.include_router(pages.router)

# Middleware para logs de erro
@app.middleware("http")
async def error_handler(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor"}
        )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="error"  # Apenas erros
    )