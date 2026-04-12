from utils.db_config import DB_CONFIG
import psycopg2
import bcrypt

def verificar_login(usuario_digitado, senha_digitada):
    """Consulta o banco, busca o hash e verifica se a senha bate."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        query = "SELECT pass FROM login WHERE usuario = %s"
        cur.execute(query, (usuario_digitado,))
        resultado = cur.fetchone()

        cur.close()

        if resultado:
            hash_no_banco = resultado[0]
            
            if bcrypt.checkpw(senha_digitada.encode('utf-8'), hash_no_banco.encode('utf-8')):
                return True
        
        return False

    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return False
    finally:
        if conn:
            conn.close()