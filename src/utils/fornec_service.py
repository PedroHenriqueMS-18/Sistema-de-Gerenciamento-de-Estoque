import psycopg2
from utils.logger import registrar_log
from utils.db_config import DB_CONFIG
from tkinter import messagebox

def buscar_fornecedores_db(termo_busca="", mostrar_inativos=0, filtro="Nome"):
    """Busca fornecedores baseada no termo, no status e no campo selecionado (ID, Nome ou CNPJ)."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Selecionamos os campos conforme a estrutura da tabela de fornecedores
        query = "SELECT id, nome_fantasia, cnpj, telefone, ativo FROM fornecedores"
        
        filtros = []
        params = []

        if not mostrar_inativos:
            filtros.append("ativo = TRUE")

        if termo_busca:
            mapeamento = {
                "ID": "id",
                "Nome": "nome_fantasia",
                "CNPJ": "cnpj"
            }
            coluna_selecionada = mapeamento.get(filtro, "nome_fantasia")

            if filtro == "ID":
                if termo_busca.isdigit():
                    filtros.append(f"{coluna_selecionada} = %s")
                    params.append(int(termo_busca))
                else:
                    filtros.append("id = -1") 
            else:
                filtros.append(f"{coluna_selecionada} ILIKE %s")
                params.append(f"%{termo_busca}%")

        if filtros:
            query += " WHERE " + " AND ".join(filtros)
        
        query += " ORDER BY nome_fantasia ASC"

        cur.execute(query, params)
        return cur.fetchall()
        
    except Exception as e:
        print(f"Erro ao buscar fornecedores: {e}")
        return []
    finally:
        if conn: conn.close()

def buscar_fornecedor_por_id(fornec_id):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Selecionamos todos os campos para o Modal de Edição
        query = "SELECT id, nome_fantasia, razao_social, cnpj, telefone, email, endereco, ativo FROM fornecedores WHERE id = %s"
        cur.execute(query, (fornec_id,))
        row = cur.fetchone()
        
        if row:
            return {
                "id": row[0],
                "nome_fantasia": row[1],
                "razao_social": row[2],
                "cnpj": row[3],
                "telefone": row[4],
                "email": row[5],
                "endereco": row[6],
                "ativo": row[7]
            }
        return None
    except Exception as e:
        print(f"Erro ao buscar detalhes do fornecedor: {e}")
        return None
    finally:
        if conn: conn.close()

def atualizar_fornecedor_db(dados):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. BUSCAR DADOS ATUAIS para o log de auditoria
        cur.execute("SELECT nome_fantasia, cnpj, telefone FROM fornecedores WHERE id = %s", (dados['id'],))
        antigo = cur.fetchone()

        if not antigo: return False

        # 2. EXECUTAR O UPDATE
        query = """
            UPDATE fornecedores 
            SET nome_fantasia = %s, razao_social = %s, cnpj = %s, telefone = %s, email = %s, endereco = %s 
            WHERE id = %s
        """
        valores = (
            dados['nome_fantasia'], dados['razao_social'], dados['cnpj'],
            dados['telefone'], dados['email'], dados['endereco'], dados['id']
        )
        cur.execute(query, valores)

        # 3. COMPARAR MUDANÇAS para o Log
        mudancas = []
        labels = ["Nome", "CNPJ", "Telefone"]
        for i, label in enumerate(labels):
            novo_valor = [dados['nome_fantasia'], dados['cnpj'], dados['telefone']][i]
            if antigo[i] != novo_valor:
                mudancas.append(f"{label}: '{antigo[i]}' -> '{novo_valor}'")

        detalhes_finais = " | ".join(mudancas) if mudancas else "Dados salvos sem alterações."

        # 4. REGISTRAR LOG
        registrar_log(
            cursor=cur,
            acao="ATUALIZAÇÃO FORNECEDOR",
            tabela="fornecedores",
            registro_id=dados['id'],
            detalhes=detalhes_finais
        )

        conn.commit()
        cur.close()
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro ao atualizar fornecedor: {e}")
        return False
    finally:
        if conn: conn.close()

def cadastrar_fornecedor_db(dados):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        query = """
            INSERT INTO fornecedores (nome_fantasia, razao_social, cnpj, telefone, email, endereco) 
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """
        valores = (
            dados['nome_fantasia'], dados['razao_social'], dados['cnpj'],
            dados['telefone'], dados['email'], dados['endereco']
        )
        
        cur.execute(query, valores)
        novo_id = cur.fetchone()[0]

        from utils.auth import UsuarioSessao
        detalhe_log = f"O administrador {UsuarioSessao.nome} cadastrou o fornecedor: {dados['nome_fantasia']} | CNPJ: {dados['cnpj']}"

        registrar_log(
            cursor=cur,
            acao="CADASTRO FORNECEDOR",
            tabela="fornecedores",
            registro_id=novo_id,
            detalhes=detalhe_log
        )

        conn.commit()
        cur.close()
        return True
    except Exception as e:
        if conn: conn.rollback()
        messagebox.showerror("Erro", f"Erro ao cadastrar fornecedor: {e}")
        return False
    finally:
        if conn: conn.close()

# Funções de status simplificadas
def alterar_status_fornecedor_db(fornec_id, status):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = "UPDATE fornecedores SET ativo = %s WHERE id = %s"
        cur.execute(query, (status, fornec_id))

        acao = "REATIVAÇÃO" if status else "INATIVAÇÃO"
        registrar_log(
            cursor=cur,
            acao=acao,
            tabela="fornecedores",
            registro_id=fornec_id,
            detalhes=f"{acao} realizada pelo sistema."
        )

        conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()