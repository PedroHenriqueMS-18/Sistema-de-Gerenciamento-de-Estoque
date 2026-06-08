# utils/produto_service.py
from utils.auth import supabase_client, UsuarioSessao
from utils.logger import registrar_log

def buscar_produtos_db(termo_busca="", mostrar_tudo=0, filtro="Nome"):
    """Busca produtos baseada no termo, no status e no campo selecionado via Supabase API."""
    try:
        # 🚀 Iniciamos a query selecionando as colunas necessárias
        query = supabase_client.table("produtos").select("id, cod_ean, nome, ativo")
        
        # 1. Filtro de Ativos (Se mostrar_tudo for 0/Falso, traz apenas ativos)
        if not mostrar_tudo:
            query = query.eq("ativo", True)

        # 2. Lógica Dinâmica de Busca baseada no OptionMenu do seu Front
        if termo_busca:
            mapeamento = {
                "ID": "id",
                "Código EAN": "cod_ean",
                "Nome": "nome"
            }
            coluna_selecionada = mapeamento.get(filtro, "nome")

            if filtro == "ID":
                if termo_busca.isdigit():
                    query = query.eq("id", int(termo_busca))
                else:
                    query = query.eq("id", -1)
            else:
                # Para Nome e EAN, usamos o ilike (busca parcial case-insensitive)
                query = query.ilike(coluna_selecionada, f"%{termo_busca}%")
        
        # 3. 💡 CORREÇÃO AQUI: No Supabase Python, usamos apenas desc=False para ordem crescente
        query = query.order("nome", desc=False)
        
        response = query.execute()
        dados = response.data if response.data else []

        # 🔄 COMPATIBILIDADE: Monta a lista de tuplas para a sua interface gráfica
        lista_tuplas = []
        for p in dados:
            # Pegamos usando .get de forma flexível caso o banco use 'ean' ou 'cod_ean'
            p_id = p.get("id")
            p_ean = p.get("cod_ean") or p.get("ean") or ""
            p_nome = p.get("nome") or ""
            lista_tuplas.append((p_id, p_ean, p_nome))
            
        return lista_tuplas
        
    except Exception as e:
        print(f"❌ Erro ao buscar produtos no Supabase: {e}")
        return []


def buscar_detalhes_produto_por_id(id_produto):
    """Busca o produto completo e formata as chaves para simular o RealDictCursor antigo."""
    try:
        response = supabase_client.table("produtos").select("*").eq("id", id_produto).execute()
        
        if response.data:
            p_antigo = response.data[0]
            
            # 🔄 MAPEAMENTO: O seu modal espera receber chaves curtas como 'ean' e 'qtd'.
            # Fazemos essa tradução aqui para não quebrar a abertura do modal gráfico!
            detalhes_formatados = {
                "id": p_antigo.get("id"),
                "ean": p_antigo.get("cod_ean"),
                "nome": p_antigo.get("nome"),
                "preco": p_antigo.get("preco"),
                "qtd": p_antigo.get("quantidade"),
                "categoria": p_antigo.get("categoria"),
                "ativo": p_antigo.get("ativo"),
                "fornecedor_id": p_antigo.get("fornecedor_id")
            }
            return detalhes_formatados
        return None
    except Exception as e:
        print(f"❌ Erro ao buscar detalhes do produto: {e}")
        return None


def inativar_produto_db(id_produto):
    """Executa o Soft Delete na nuvem e valida o sucesso real da operação."""
    try:
        print(f"🔄 Tentando inativar produto ID: {id_produto}")
        
        # Executa o update na nuvem
        response = supabase_client.table("produtos").update({"ativo": False}).eq("id", int(id_produto)).execute()
        
        # 💡 A MÁGICA AQUI: Se chegou até aqui sem disparar o 'except', o banco processou!
        # Conferimos se a resposta não é nula.
        if response is not None:
            print(f"✅ Produto {id_produto} inativado com sucesso na nuvem.")
            
            try:
                registrar_log(
                    cursor=None,
                    acao="INATIVAÇÃO",
                    tabela="produtos",
                    registro_id=id_produto,
                    detalhes=f"Inativou o produto (ID: {id_produto})"
                )
            except Exception as log_err:
                print(f"⚠️ Erro ao registrar log de auditoria: {log_err}")

            return True # Retorna True para o modal saber que deu certo!
        return False
            
    except Exception as e:
        print(f"❌ Erro crítico ao inativar produto: {e}")
        return False


def reativar_produto_bd(id_produto):
    """Ativa novamente o produto na nuvem."""
    try:
        print(f"🔄 Tentando reativar produto ID: {id_produto}")
        
        response = supabase_client.table("produtos").update({"ativo": True}).eq("id", int(id_produto)).execute()
        
        if response is not None:
            print(f"✅ Produto {id_produto} reativado com sucesso.")
            try:
                registrar_log(
                    cursor=None,
                    acao="REATIVAÇÃO",
                    tabela="produtos",
                    registro_id=id_produto,
                    detalhes=f"Reativou o produto (ID: {id_produto})"
                )
            except Exception as log_err:
                print(f"⚠️ Erro ao registrar log: {log_err}")
            return True
        return False
    except Exception as e:
        print(f"❌ Erro crítico ao reativar produto: {e}")
        return False


def atualizar_produto_db(novos_dados):
    """Executa a atualização dos dados tratando o retorno de forma estável."""
    try:
        p_id = int(novos_dados['id'])
        print(f"🔄 Iniciando atualização do produto ID: {p_id}")

        # 1. BUSCAR DADOS ANTIGOS PARA O LOG
        antigo = {}
        try:
            res_antigo = supabase_client.table("produtos").select("nome, preco, quantidade, categoria, cod_ean, fornecedor_id").eq("id", p_id).execute()
            if res_antigo and res_antigo.data:
                antigo = res_antigo.data[0]
        except Exception as err_busca:
            print(f"⚠️ Falha na busca de auditoria: {err_busca}")

        # 2. TRATAMENTO DOS VALORES
        preco_novo = float(str(novos_dados['preco']).replace(',', '.'))
        qtd_nova = int(novos_dados['qtd'])
        fornec_id_novo = novos_dados.get('fornecedor_id')
        if fornec_id_novo is not None:
            fornec_id_novo = int(fornec_id_novo)

        valores_update = {
            "nome": novos_dados['nome'],
            "preco": preco_novo,
            "quantidade": qtd_nova,
            "categoria": novos_dados['categoria'],
            "cod_ean": novos_dados['ean'],
            "fornecedor_id": fornec_id_novo
        }
        
        # 3. EXECUTAR UPDATE
        res_update = supabase_client.table("produtos").update(valores_update).eq("id", p_id).execute()

        if res_update is None:
            print("❌ O Supabase retornou uma resposta nula no Update.")
            return False

        print(f"✅ Produto {p_id} atualizado com sucesso na nuvem.")

        # 4. GERAÇÃO DO LOG DE AUDITORIA
        if antigo:
            try:
                mudancas = []
                if antigo.get("nome") != novos_dados['nome']:
                    mudancas.append(f"Nome: {antigo.get('nome')} -> {novos_dados['nome']}")
                if float(antigo.get("preco") or 0) != preco_novo:
                    mudancas.append(f"Preço: {antigo.get('preco')} -> {preco_novo}")
                if int(antigo.get("quantidade") or 0) != qtd_nova:
                    mudancas.append(f"Qtd: {antigo.get('quantidade')} -> {qtd_nova}")
                if antigo.get("categoria") != novos_dados['categoria']:
                    mudancas.append(f"Categoria: {antigo.get('categoria')} -> {novos_dados['categoria']}")
                if antigo.get("cod_ean") != novos_dados['ean']:
                    mudancas.append(f"EAN: {antigo.get('cod_ean')} -> {novos_dados['ean']}")
                if antigo.get("fornecedor_id") != fornec_id_novo:
                    mudancas.append(f"Fornecedor ID: {antigo.get('fornecedor_id')} -> {fornec_id_novo}")

                detalhes_finais = " | ".join(mudancas) if mudancas else "Nenhuma alteração de valor realizada."

                registrar_log(
                    cursor=None,
                    acao="ATUALIZAÇÃO",
                    tabela="produtos",
                    registro_id=p_id,
                    detalhes=detalhes_finais
                )
            except Exception as log_err:
                print(f"⚠️ Erro ao gerar log de alteração: {log_err}")
            
        return True # Retorna True com sucesso!

    except Exception as e:
        print(f"❌ Erro crítico ao atualizar produto no Supabase: {e}")
        return False