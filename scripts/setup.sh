#!/bin/bash

echo "🚀 Iniciando setup do Telegram Bot Manager..."

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 não encontrado${NC}"
    exit 1
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não encontrado${NC}"
    exit 1
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose não encontrado${NC}"
    exit 1
fi

echo "✅ Dependências verificadas"

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cp .env.example .env
    echo -e "${GREEN}✅ Arquivo .env criado${NC}"
else
    echo "✅ Arquivo .env já existe"
fi

# Iniciar containers
echo "🐳 Iniciando containers Docker..."
docker-compose up -d

# Aguardar containers inicializarem
echo "⏳ Aguardando containers..."
sleep 5

# Verificar status
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Containers iniciados${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar containers${NC}"
    exit 1
fi

# Instalar dependências Python
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

# Inicializar banco de dados
echo "🗄️ Inicializando banco de dados..."
python scripts/init_db.py

echo ""
echo -e "${GREEN}✅ Setup concluído com sucesso!${NC}"
echo ""
echo "📋 Próximos passos:"
echo "   1. Configure o SERVER_URL no arquivo .env"
echo "   2. Execute: uvicorn app.main:app --reload"
echo "   3. Execute: python worker/main.py"
echo "   4. Acesse: http://localhost:8000"
echo ""
echo "Para usar webhooks externos:"
echo "   ngrok http 8000"