import asyncio
import signal
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker.processors import MessageProcessor
from app.redis.client import redis_client
from app.database.connection import AsyncSessionLocal
import time

class Worker:
    def __init__(self):
        self.running = True
        self.processor = MessageProcessor()
        
    def signal_handler(self, sig, frame):
        """Handler para shutdown gracioso"""
        print("\n🔄 Encerrando worker...")
        self.running = False
    
    async def process_queue(self):
        """Processar fila de updates"""
        print("🚀 Worker iniciado - Processando fila...")
        
        while self.running:
            try:
                # Pegar item da fila
                update_data = await redis_client.get_from_queue('telegram_updates', timeout=1)
                
                if update_data:
                    print(f"📦 Processando update do bot {update_data['bot_id']}")
                    
                    # Processar com nova sessão do banco
                    async with AsyncSessionLocal() as db:
                        await self.processor.process_update(
                            db,
                            update_data['bot_id'],
                            update_data['update']
                        )
                
                await asyncio.sleep(0.1)  # Pequena pausa
                
            except Exception as e:
                print(f"❌ Erro no worker: {str(e)}")
                await asyncio.sleep(1)
    
    async def run(self):
        """Executar worker"""
        # Configurar signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🔄 Conectando ao sistema...")
        await redis_client.connect()
        
        # Criar múltiplas tasks para processar em paralelo
        tasks = []
        for i in range(3):  # 3 workers paralelos
            print(f"✅ Worker {i+1} iniciado")
            task = asyncio.create_task(self.process_queue())
            tasks.append(task)
        
        # Aguardar todas as tasks
        await asyncio.gather(*tasks)
        
        print("✅ Worker encerrado")

if __name__ == "__main__":
    print("="*50)
    print("🤖 TELEGRAM BOT WORKER")
    print("="*50)
    worker = Worker()
    asyncio.run(worker.run())