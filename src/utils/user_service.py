import psycopg2
from utils.db_config import DB_CONFIG

def buscar_usuarios_db(termo_busca="", mostrar_inativos=0, filtro="Nome"):
    """Busca usuários baseada no termo, no status e no campo selecionado (ID, Nome ou Usuário)."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Selecionamos os campos que definimos para a tabela de usuários
        query = "SELECT id, nome, usuario, nivel, ativo FROM login"
        
        filtros = []
        params = []

        # 1. Filtro de Status (Ativo/Inativo)
        if not mostrar_inativos:
            filtros.append("ativo = TRUE")

        # 2. Lógica Dinâmica de Busca
        if termo_busca:
            mapeamento = {
                "ID": "id",
                "Nome": "nome",
                "Usuário": "usuario"
            }
            coluna_selecionada = mapeamento.get(filtro, "nome")

            if filtro == "ID":
                if termo_busca.isdigit():
                    filtros.append(f"{coluna_selecionada} = %s")
                    params.append(int(termo_busca))
                else:
                    filtros.append("id = -1") 
            else:
                # Busca parcial para Nome e Login (Usuário)
                filtros.append(f"{coluna_selecionada} ILIKE %s")
                params.append(f"%{termo_busca}%")

        # 3. Montagem da Query
        if filtros:
            query += " WHERE " + " AND ".join(filtros)
        
        query += " ORDER BY nome ASC"

        cur.execute(query, params)
        return cur.fetchall()
        
    except Exception as e:
        print(f"Erro ao buscar usuários: {e}")
        return []
    finally:
        if conn: 
            conn.close()

def buscar_usuario_por_id(user_id):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Selecionamos tudo que o modal precisa
        query = "SELECT id, nome, usuario, nivel, ativo, cpf FROM login WHERE id = %s"
        cur.execute(query, (user_id,))
        row = cur.fetchone()
        
        if row:
            # Transformamos em dicionário para o Modal ler fácil
            return {
                "id": row[0],
                "nome": row[1],
                "login": row[2],
                "nivel": row[3],
                "ativo": row[4],
                "cpf": row[5]
            }
        return None
    except Exception as e:
        print(f"Erro ao buscar detalhes: {e}")
        return None
    finally:
        if conn: conn.close()

# No topo do arquivo: from utils.db_config import get_connection (ou como você chama sua conexão)

def atualizar_usuario_db(dados):
    """Atualiza nome, login e nível do usuário no banco."""
    # Sua lógica de UPDATE usuarios SET nome=%s, login=%s, nivel=%s WHERE id=%s
    pass

def inativar_usuario_db(usuario_id):
    """Muda o status do usuário para inativo (ativo = False)."""
    # Sua lógica de UPDATE usuarios SET ativo=False WHERE id=%s
    pass

def reativar_usuario_db(usuario_id):
    """Muda o status do usuário para ativo (ativo = True)."""
    # Sua lógica de UPDATE usuarios SET ativo=True WHERE id=%s
    pass