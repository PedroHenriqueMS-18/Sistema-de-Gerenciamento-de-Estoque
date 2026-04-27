# utils/produto_service.py
import psycopg2
import psycopg2.extras
from utils.db_config import DB_CONFIG
from utils.logger import registrar_log
from utils.auth import UsuarioSessao

def buscar_produtos_db(termo_busca="", mostrar_tudo=0, filtro="Nome"):
    """Busca produtos baseada no termo, no status e agora no campo selecionado."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = "SELECT id, cod_ean, nome FROM produtos"
        
        filtros = []
        params = []

        # 1. Filtro de Ativos (Continua igual)
        if not mostrar_tudo:
            filtros.append("ativo = TRUE")

        # 2. Lógica Dinâmica de Busca (Onde a mágica acontece)
        if termo_busca:
            # Mapeamos o texto do OptionMenu para a coluna real do banco
            mapeamento = {
                "ID": "id",
                "Código EAN": "cod_ean",
                "Nome": "nome"
            }
            coluna_selecionada = mapeamento.get(filtro, "nome")

            # Se for ID, a busca costuma ser exata (=)
            if filtro == "ID":
                if termo_busca.isdigit(): # Só filtra se for número para não quebrar o SQL
                    filtros.append(f"{coluna_selecionada} = %s")
                    params.append(int(termo_busca))
                else:
                    # Se digitaram letra no ID, forçamos um filtro que não trará nada
                    filtros.append("id = -1") 
            else:
                # Para Nome e EAN, usamos o ILIKE para busca parcial (contém)
                filtros.append(f"{coluna_selecionada} ILIKE %s")
                params.append(f"%{termo_busca}%")

        # 3. Montagem Dinâmica
        if filtros:
            query += " WHERE " + " AND ".join(filtros)
        
        query += " ORDER BY nome ASC"

        cur.execute(query, params)
        return cur.fetchall()
        
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

        detalhe = f"Inativou o produto (ID: {id_produto})"

        registrar_log(
            cursor=cur,
            acao="INATIVAÇÃO",
            tabela="produtos",
            registro_id=id_produto,
            detalhes=detalhe
        )
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

        detalhe = f"Reativou o produto (ID: {id_produto})"

        registrar_log(
            cursor=cur,
            acao="REATIVAÇÃO",
            tabela="produtos",
            registro_id=id_produto,
            detalhes=detalhe
        )

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
    """Executa o UPDATE dos dados do produto e registra a auditoria incluindo o fornecedor."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. BUSCAR DADOS ANTIGOS (Incluindo o fornecedor_id)
        cur.execute("SELECT nome, preco, quantidade, categoria, cod_ean, fornecedor_id FROM produtos WHERE id = %s", (novos_dados['id'],))
        antigo = cur.fetchone()

        if not antigo:
            return False 

        # 2. TRATAMENTO DOS NOVOS VALORES
        preco_novo = float(str(novos_dados['preco']).replace(',', '.'))
        qtd_nova = int(novos_dados['qtd'])
        fornec_id_novo = novos_dados.get('fornecedor_id') # Pega o ID que veio do modal

        # 3. EXECUTAR O UPDATE
        query = """
            UPDATE produtos 
            SET nome = %s, preco = %s, quantidade = %s, categoria = %s, cod_ean = %s, fornecedor_id = %s
            WHERE id = %s
        """
        valores = (
            novos_dados['nome'],
            preco_novo,
            qtd_nova,
            novos_dados['categoria'],
            novos_dados['ean'],
            fornec_id_novo, # Novo campo!
            novos_dados['id']
        )
        cur.execute(query, valores)

        # 4. IDENTIFICAR O QUE MUDOU (A "Fofoca")
        mudancas = []
        # ... (suas verificações de nome, preço, etc permanecem iguais)
        
        # Nova verificação para o fornecedor no log
        if antigo[5] != fornec_id_novo:
            mudancas.append(f"Fornecedor ID: {antigo[5]} -> {fornec_id_novo}")

        detalhes_finais = " | ".join(mudancas) if mudancas else "Nenhuma alteração de valor realizada."

        # 5. REGISTRAR NO LOG
        registrar_log(
            cursor=cur,
            acao="ATUALIZAÇÃO",
            tabela="produtos",
            registro_id=novos_dados['id'],
            detalhes=detalhes_finais
        )

        conn.commit()
        cur.close()
        return True

    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro ao atualizar produto: {e}")
        return False
    finally:
        if conn: conn.close()
