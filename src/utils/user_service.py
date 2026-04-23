import psycopg2
from utils.logger import registrar_log
from utils.db_config import DB_CONFIG
from tkinter import messagebox
import bcrypt

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
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. BUSCAR DADOS ATUAIS (O "Antes") para comparação
        # Buscamos as colunas que podem ser alteradas
        cur.execute("SELECT nome, usuario, cpf, nivel FROM login WHERE id = %s", (dados['id'],))
        antigo = cur.fetchone()

        if not antigo:
            return False

        # 2. EXECUTAR O UPDATE
        query = "UPDATE login SET nome = %s, usuario = %s, cpf = %s, nivel = %s WHERE id = %s"
        
        nivel_novo = int(dados['nivel'])
        id_usuario_alvo = int(dados['id'])
        
        novos_valores = (
            dados['nome'],
            dados['login'],
            dados['cpf'],
            nivel_novo,
            id_usuario_alvo
        )

        cur.execute(query, novos_valores)

        # 3. COMPARAR AS MUDANÇAS (A "Fofoca" técnica)
        mudancas = []
        if antigo[0] != dados['nome']:
            mudancas.append(f"Nome: '{antigo[0]}' -> '{dados['nome']}'")
        
        if antigo[1] != dados['login']:
            mudancas.append(f"Login: '{antigo[1]}' -> '{dados['login']}'")
            
        if antigo[2] != dados['cpf']:
            mudancas.append(f"CPF: {antigo[2]} -> {dados['cpf']}")
            
        if int(antigo[3]) != nivel_novo:
            mudancas.append(f"Nível: {antigo[3]} -> {nivel_novo}")

        # Se não houver mudanças, avisamos no log
        detalhes_finais = " | ".join(mudancas) if mudancas else "Dados salvos sem alterações."

        # 4. REGISTRAR O LOG (Importando a sua função genérica)
        
        registrar_log(
            cursor=cur,
            acao="ALTERAÇÃO DE PERFIL",
            tabela="login", # Nome da sua tabela de usuários
            registro_id=id_usuario_alvo,
            detalhes=detalhes_finais
        )

        # 5. COMMIT (Salva o UPDATE e o LOG juntos)
        conn.commit()
        cur.close()
        return True

    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro ao atualizar e logar usuário: {e}")
        return False
    finally:
        if conn:
            conn.close()

def inativar_usuario_db(usuario_id):
    """Muda o status do usuário para inativo (ativo = False)."""
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = "UPDATE login SET ativo = FALSE WHERE id = %s"

        cur.execute(query, (usuario_id,))

        detalhe = f"Inativou o produto (ID: {usuario_id})"

        registrar_log(
            cursor=cur,
            acao="INATIVAÇÃO",
            tabela="produtos",
            registro_id=usuario_id,
            detalhes=detalhe
        )

        conn.commit()
        cur.close
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro ao inativar {e}")
        return False
    finally:
        if conn: conn.close()

def reativar_usuario_db(usuario_id):
    """Muda o status do usuário para ativo (ativo = True)."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = "UPDATE login SET ativo = TRUE WHERE id = %s"

        cur.execute(query, (usuario_id,))

        detalhe = f"Reativou o produto (ID: {usuario_id})"

        registrar_log(
            cursor=cur,
            acao="REATIVAÇÃO",
            tabela="produtos",
            registro_id=usuario_id,
            detalhes=detalhe
        )
        conn.commit()
        cur.close
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro ao inativar {e}")
        return False
    finally:
        if conn: conn.close()

def cadastrar_usuario_db(dados):
    senha_plana = dados['senha'].encode('utf-8')
    hash_gerado = bcrypt.hashpw(senha_plana, bcrypt.gensalt())

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        query = "INSERT INTO login (nome, cpf, usuario, nivel, pass) VALUES (%s, %s, %s, %s, %s)"
        valores = (
                    dados['nome'],
                    dados['cpf'],
                    dados['login'],
                    dados['nivel'],
                    hash_gerado.decode('utf-8')
                )
        cur.execute(query, valores)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Erro no banco: {e}")
        return False
    finally:
        if conn: conn.close()
    

