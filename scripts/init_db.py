#!/usr/bin/env python3
"""Script para inicializar o banco de dados"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import sync_engine
from app.database.models import Base

def init_database():
    """Criar todas as tabelas no banco"""
    print("🔄 Criando tabelas no banco de dados...")
    
    try:
        Base.metadata.create_all(bind=sync_engine)
        print("✅ Tabelas criadas com sucesso!")
        
        # Listar tabelas criadas
        print("\n📋 Tabelas criadas:")
        for table in Base.metadata.tables:
            print(f"   - {table}")
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()