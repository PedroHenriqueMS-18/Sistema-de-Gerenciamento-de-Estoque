import psycopg2
import os
from dotenv import load_dotenv

""" Carrega as variáveis de ambiente definidas no arquivo '.env' para o sistema. """
load_dotenv()

"""Gerencia a conexão e as operações básicas no banco de dados PostgreSQL."""
class Database:
    
    """Inicializa a instância, estabelece conexão e garante a criação da tabela base."""
    def __init__(self):
        self.conn = None
        self.connect()
        self.create_table()

    """Estabelece a conexão com o PostgreSQL usando variáveis de ambiente do arquivo .env."""
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD")
            )
            print("Conexão com o PostgreSQL realizada com sucesso!")
        except Exception as e:
            print(f"Erro ao conectar com o banco {e}")
        
    """Executa comandos SQL de alteração (INSERT, UPDATE, DELETE) e realiza o commit."""
    def execute_query(self, query, params=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Erro na query {e}")
            self.conn.rollback()
    
    """Cria a tabela 'produtos' no banco de dados caso ela ainda não exista."""
    def create_table(self):
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
        print("Tabela 'produtos' pronta para uso")

    """Executa uma consulta de seleção (SELECT) e retorna todos os registros encontrados."""
    def fetch_all(self, query, params=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"Erro ao buscar dados {e}")
            return []

if __name__ == "__main__":
    db = Database()