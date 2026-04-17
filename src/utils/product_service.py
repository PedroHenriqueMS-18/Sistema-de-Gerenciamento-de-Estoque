# utils/produto_service.py
import psycopg2
import psycopg2.extras
from utils.db_config import DB_CONFIG

def buscar_produtos_db(termo_busca="", mostrar_tudo=0):
    """Retorna apenas o essencial para a lista principal, mantendo os filtros."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Base da Query - AGORA SÓ COM 3 COLUNAS
        # Note que não pedimos 'ativo', 'preco', etc., no SELECT
        query = "SELECT id, cod_ean, nome FROM produtos"
        
        filtros = []
        params = []

        # 2. Lógica do Checkbox (Filtro de Ativos)
        # O filtro continua funcionando no WHERE, mesmo que a coluna não esteja no SELECT
        if not mostrar_tudo:
            filtros.append("ativo = TRUE")

        # 3. Lógica da Busca (Nome)
        if termo_busca:
            filtros.append("nome ILIKE %s")
            params.append(f"%{termo_busca}%")

        # 4. Montagem Dinâmica
        if filtros:
            query += " WHERE " + " AND ".join(filtros)
        
        # 5. Ordenação
        query += " ORDER BY nome ASC"

        cur.execute(query, params)
        return cur.fetchall() # Retornará apenas tuplas de 3 itens (id, ean, nome)
        
    except Exception as e:
        print(f"Erro ao buscar: {e}")
        return []
    finally:
        if conn: 
            conn.close()

def buscar_detalhes_produto_por_id(id_produto):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Mantemos o 'ativo' aqui para o Python saber qual botão desenhar
        query = """
            SELECT 
                id, 
                cod_ean AS ean, 
                nome, 
                preco, 
                quantidade AS qtd, 
                categoria, 
                ativo 
            FROM produtos 
            WHERE id = %s
        """
        
        cur.execute(query, (id_produto,))
        return cur.fetchone()
    except Exception as e:
        print(f"Erro ao buscar detalhes: {e}")
        return None
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
            SET nome = %s, preco = %s, quantidade = %s, categoria = %s,
            cod_ean = %s
            WHERE id = %s
        """
        
        # O tratamento de tipos (float/int) pode ficar aqui no serviço
        valores = (
            novos_dados['nome'],
            float(str(novos_dados['preco']).replace(',', '.')),
            int(novos_dados['qtd']),
            novos_dados['categoria'],
            novos_dados['ean'],
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