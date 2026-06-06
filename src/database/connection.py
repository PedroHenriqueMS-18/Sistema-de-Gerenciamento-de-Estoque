import os
from dotenv import load_dotenv
from supabase import create_client, Client
import sys

# Força o Python a ler o arquivo .env
load_dotenv()

class Database:
    
    def __init__(self):
        self.client = None
        self.connect()

    def connect(self):
        try:
            print("🔄 Carregando credenciais ocultas do .env...")
            
            # Buscando as variáveis de ambiente sem expor no código
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")
            
            if not url or not key:
                raise ValueError("❌ Erro: SUPABASE_URL ou SUPABASE_ANON_KEY não foram encontradas no arquivo .env!")

            print("🔄 Conectando ao Supabase através da API Client oficial...")
            self.client = create_client(url, key)
            print("🚀 CONEXÃO REALIZADA COM SUCESSO ABSOLUTO VIA CLIENT SDK!")
            
        except Exception as e:
            print("\n❌ ERRO FATAL NO CLIENTE OFICIAL:")
            print(f"👉 Detalhes do erro: {e}\n")
            self.client = None
            sys.exit(1)
        
    """Executa comandos SQL de alteração (INSERT, UPDATE, DELETE) e realiza o commit."""
    def execute_query(self, query, params=None):
        if not self.conn:
            print("⚠️ Operação cancelada: Não há conexão ativa com o banco de dados.")
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            cursor.close()
        except Exception as e:
            print(f"❌ Erro na query: {e}")
            if self.conn:
                self.conn.rollback()
    
    """Cria a tabela 'produtos' no banco de dados caso ela ainda não exista."""
    def create_table(self):
        # Como já criamos via SQL Editor, isso aqui serve como contingência segura
        query = """
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            preco DECIMAL(10, 2) NOT NULL,
            quantidade INTEGER NOT NULL,
            categoria VARCHAR(50)
        );
        """
        self.execute_query(query)

    """Executa uma consulta de seleção (SELECT) e retorna todos os registros encontrados."""
    def fetch_all(self, query, params=None):
        if not self.conn:
            print("⚠️ Operação cancelada: Não há conexão ativa com o banco de dados.")
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"❌ Erro ao buscar dados: {e}")
            return []

if __name__ == "__main__":
    db = Database()