from utils.db_config import DB_CONFIG
import psycopg2
# Certifique-se que o caminho do import está correto

def buscar_produto_por_ean(codigo_ean):
    """
    Conecta ao banco, busca o produto pelo EAN e retorna uma tupla.
    Retorna None se o produto não for encontrado ou houver erro.
    """
    conn = None
    produto = None
    
    try:
        # 1. Abre a conexão usando o seu dicionário DB_CONFIG
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 2. Define a Query (conforme sua coluna 'cod_ean')
        query = """
            SELECT id, cod_ean, nome, preco, quantidade
            FROM produtos 
            WHERE cod_ean = %s
        """
        
        # 3. Executa a busca
        cursor.execute(query, (codigo_ean,))
        produto = cursor.fetchone() 
        
        # 4. Fecha o cursor
        cursor.close()

    except Exception as e:
        print(f"ERRO DE BANCO DE DADOS: {e}")
        # Aqui você poderia disparar um log ou um alerta
        return None
        
    finally:
        # 5. GARANTE que a conexão será fechada, mesmo se der erro
        if conn is not None:
            conn.close()
            
    return produto