# utils/produto_service.py
import psycopg2
from utils.db_config import DB_CONFIG

def buscar_produtos_ativos_db(termo_busca="", mostrar_tudo=0):
    """Esta função só conversa com o Banco de Dados."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Base da Query
        query = "SELECT id, nome, preco, quantidade, categoria, ativo FROM produtos"
        filtros = []
        params = []

        # 2. Lógica do Checkbox
        if not mostrar_tudo:
            filtros.append("ativo = TRUE")

        # 3. Lógica da Busca
        if termo_busca:
            filtros.append("nome ILIKE %s")
            params.append(f"%{termo_busca}%")

        # 4. Montagem Dinâmica
        if filtros:
            # O join transforma a lista em: "filtro1 AND filtro2"
            query += " WHERE " + " AND ".join(filtros)
        
        # 5. Ordenação
        query += " ORDER BY nome ASC"

        cur.execute(query, params)
        return cur.fetchall()
    except Exception as e:
        print(f"Erro ao buscar: {e}")
        return []
    finally:
        if conn: conn.close()

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

def reativar_produto_bd(id_produto):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        query = "UPDATE produtos SET ativo = TRUE WHERE id = %s"
        cur.execute(query, (id_produto,))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro ao reativar: {e}")
        return False
    finally:
        if conn: conn.close()

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