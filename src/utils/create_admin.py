from utils.db_config import DB_CONFIG
import psycopg2
import bcrypt

USUARIO_NOVO = "admin"
SENHA_NOVA = "123"

def executar_cadastro_direto():
    """Gera o hash da senha via bcrypt e insere o novo usuário no banco PostgreSQL."""
    conn = None
    try:
        salt = bcrypt.gensalt()
        senha_hash = bcrypt.hashpw(SENHA_NOVA.encode('utf-8'), salt)

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        query = "INSERT INTO login (usuario, pass) VALUES (%s, %s)"
        cur.execute(query, (USUARIO_NOVO, senha_hash.decode('utf-8')))

        conn.commit()
        cur.close()
        print("✅ Sucesso!")

    except Exception as e:
        print(f"❌ Erro: {e}")
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    executar_cadastro_direto()