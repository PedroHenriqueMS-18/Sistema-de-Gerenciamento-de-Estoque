from utils.auth import supabase_client, UsuarioSessao
from utils.logger import registrar_log
from tkinter import messagebox

def buscar_fornecedores_db(termo_busca="", mostrar_inativos=0, filtro="Nome"):
    """Busca fornecedores no Supabase baseada no termo, no status e no campo selecionado."""
    try:
        # Iniciamos a base da Query selecionando as colunas necessárias
        query = supabase_client.table("fornecedores").select("id, nome_fantasia, cnpj, telefone, ativo")
        
        # Se mostrar_inativos for falso/zero, aplicamos o filtro para trazer só ativos
        if not mostrar_inativos:
            query = query.eq("ativo", True)

        # Filtros dinâmicos com encadeamento de métodos (o "mais" que conversamos!)
        if termo_busca:
            mapeamento = {
                "ID": "id",
                "Nome": "nome_fantasia",
                "CNPJ": "cnpj"
            }
            coluna_selecionada = mapeamento.get(filtro, "nome_fantasia")

            if filtro == "ID":
                if termo_busca.isdigit():
                    query = query.eq(coluna_selecionada, int(termo_busca))
                else:
                    query = query.eq("id", -1) # Evita erro de conversão forçando busca vazia
            else:
                # Busca parcial (LIKE) na nuvem desconsiderando maiúsculas/minúsculas
                query = query.ilike(coluna_selecionada, f"%{termo_busca}%")
        
        # Ordenação em ordem ascendente (A-Z)
        query = query.order("nome_fantasia", desc=False)
        response = query.execute()

        # Convertemos a lista de dicionários para uma lista de tuplas para manter compatibilidade com sua UI
        dados_tupla = []
        if response.data:
            for item in response.data:
                dados_tupla.append((
                    item.get("id"),
                    item.get("nome_fantasia"),
                    item.get("cnpj"),
                    item.get("telefone"),
                    item.get("ativo")
                ))
        return dados_tupla
        
    except Exception as e:
        print(f"❌ Erro ao buscar fornecedores no Supabase: {e}")
        return []

def buscar_fornecedor_por_id(fornec_id):
    """Busca todos os detalhes de um único fornecedor pelo ID."""
    try:
        response = supabase_client.table("fornecedores").select("*").eq("id", fornec_id).execute()
        
        if response.data:
            # Isolamos o dicionário do índice zero exatamente como você esquadrinhou!
            return response.data[0]
        return None
    except Exception as e:
        print(f"❌ Erro ao buscar detalhes do fornecedor: {e}")
        return None

def atualizar_fornecedor_db(dados):
    """Atualiza os dados de um fornecedor na nuvem e gera log de auditoria comparativo."""
    try:
        # 1. Buscamos os dados atuais diretamente na nuvem para comparar as alterações
        antigo = buscar_fornecedor_por_id(dados['id'])
        if not antigo: 
            return False

        # 2. Executamos o UPDATE enviando as novas informações
        valores_update = {
            "nome_fantasia": dados['nome_fantasia'],
            "razao_social": dados['razao_social'],
            "cnpj": dados['cnpj'],
            "telefone": dados['telefone'],
            "email": dados['email'],
            "endereco": dados['endereco']
        }
        supabase_client.table("fornecedores").update(valores_update).eq("id", dados['id']).execute()

        # 3. Comparamos as mudanças para gerar uma auditoria precisa
        mudancas = []
        campos_checagem = [
            ("Nome", "nome_fantasia"),
            ("CNPJ", "cnpj"),
            ("Telefone", "telefone")
        ]
        for label, campo in campos_checagem:
            valor_antigo = str(antigo.get(campo, ""))
            valor_novo = str(dados.get(campo, ""))
            if valor_antigo != valor_novo:
                mudancas.append(f"{label}: '{valor_antigo}' -> '{valor_novo}'")

        detalhes_finais = " | ".join(mudancas) if mudancas else "Dados salvos sem alterações."

        # 4. Registramos o Log de Auditoria na nuvem
        try:
            registrar_log(
                cursor=None,
                acao="ATUALIZAÇÃO FORNECEDOR",
                tabela="fornecedores",
                registro_id=dados['id'],
                detalhes=f"O funcionário {UsuarioSessao.nome} alterou - " + detalhes_finais
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao registrar log de alteração de fornecedor: {log_err}")

        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar fornecedor no Supabase: {e}")
        return False

def cadastrar_fornecedor_db(dados):
    """Insere um novo fornecedor na tabela da nuvem e gera o log."""
    try:
        valores_insert = {
            "nome_fantasia": dados['nome_fantasia'],
            "razao_social": dados['razao_social'],
            "cnpj": dados['cnpj'],
            "telefone": dados['telefone'],
            "email": dados['email'],
            "endereco": dados['endereco'],
            "ativo": True
        }
        
        response = supabase_client.table("fornecedores").insert(valores_insert).execute()
        
        novo_id = None
        if response.data:
            novo_id = response.data[0].get("id")

        # Geramos o detalhe do log capturando quem realizou a ação
        detalhe_log = f"O funcionário {UsuarioSessao.nome} cadastrou o fornecedor: {dados['nome_fantasia']} | CNPJ: {dados['cnpj']}"

        try:
            registrar_log(
                cursor=None,
                acao="CADASTRO FORNECEDOR",
                tabela="fornecedores",
                registro_id=novo_id,
                detalhes=detalhe_log
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao registrar log de cadastro de fornecedor: {log_err}")

        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao cadastrar fornecedor no Supabase: {e}")
        return False

def alterar_status_fornecedor_db(fornec_id, status):
    """Ativa ou Inativa um fornecedor mudando a flag lógico na tabela."""
    try:
        supabase_client.table("fornecedores").update({"ativo": status}).eq("id", fornec_id).execute()

        acao = "REATIVAÇÃO" if status else "INATIVAÇÃO"
        try:
            registrar_log(
                cursor=None,
                acao=acao,
                tabela="fornecedores",
                registro_id=fornec_id,
                detalhes=f"{acao} do fornecedor realizada por {UsuarioSessao.nome}."
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao registrar log de status do fornecedor: {log_err}")

        return True
    except Exception as e:
        print(f"❌ Erro ao alterar status do fornecedor no Supabase: {e}")
        return False