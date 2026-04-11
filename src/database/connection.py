import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
       self.conn = None
       self.connect()
       self.create_table()

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
        
    def execute_query(self, query, params=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Erro na query {e}")
            self.conn.rollback()
    
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