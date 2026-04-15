# utils/produto_service.py
import psycopg2
from utils.db_config import DB_CONFIG

def buscar_produtos_ativos_db(termo_busca=""):
    """Esta função só conversa com o Banco de Dados."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        if termo_busca == "":
            query = "SELECT id, nome, preco, quantidade, categoria FROM produtos WHERE ativo = TRUE ORDER BY nome ASC"
            params = None
        else:
            query = "SELECT id, nome, preco, quantidade, categoria FROM produtos WHERE ativo = TRUE AND nome ILIKE %s ORDER BY nome ASC"
            params = (f"%{termo_busca}%",)

        cur.execute(query, params)
        produtos_reais = cur.fetchall() # Aqui estão os dados puros
        cur.close()
        return produtos_reais # Retorna a lista de tuplas
    except Exception as e:
        print(f"Erro no banco: {e}")
        return []
    finally:
        if conn:
            conn.close()

def inativar_produto_db(id_produto):
    """Executa o Soft Delete no banco de dados."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        query = "UPDATE produtos SET ativo = FALSE WHERE id = %s"
        cur.execute(query, (id_produto,))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro ao inativar: {e}")
        return False
    finally:
        if conn:
            conn.close()

def atualizar_produto_db(novos_dados):
    """Executa o UPDATE dos dados do produto."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        query = """
            UPDATE produtos 
            SET nome = %s, preco = %s, quantidade = %s, categoria = %s 
            WHERE id = %s
        """
        
        # O tratamento de tipos (float/int) pode ficar aqui no serviço
        valores = (
            novos_dados['nome'],
            float(str(novos_dados['preco']).replace(',', '.')),
            int(novos_dados['qtd']),
            novos_dados['categoria'],
            novos_dados['id']
        )

        cur.execute(query, valores)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro ao atualizar: {e}")
        return False
    finally:
        if conn:
            conn.close()