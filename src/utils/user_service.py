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

