from utils.auth import supabase_client
from utils.logger import registrar_log

def buscar_produto_por_ean(codigo_ean):
    """
    Conecta ao Supabase, busca o produto pelo EAN e retorna uma tupla.
    Retorna None se o produto não for encontrado, estiver inativo ou houver erro.
    """
    try:
        # Buscamos o produto na nuvem que tenha o EAN correspondente e esteja ativo
        response = supabase_client.table("produtos")\
            .select("id, cod_ean, nome, preco, quantidade")\
            .eq("cod_ean", str(codigo_ean))\
            .eq("ativo", True)\
            .execute()
        
        # Se a lista .data não estiver vazia, significa que achamos o produto!
        if response.data:
            item = response.data[0] # Isolamos o dicionário do índice zero
            
            # Devolvemos os dados formatados em tupla para manter compatibilidade com sua UI
            return (
                item.get("id"),
                item.get("cod_ean"),
                item.get("nome"),
                float(item.get("preco", 0.0)),
                int(item.get("quantidade", 0))
            )
        return None

    except Exception as e:
        print(f"❌ ERRO AO BUSCAR PRODUTO POR EAN NO SUPABASE: {e}")
        return None

def buscar_produtos_pdv(termo_busca, limite=50):
    """
    Pesquisa produtos ativos no Supabase pelo código de barras (EAN) OU pelo nome/descrição.
    Utilizada pela tela de pesquisa do PDV (F1). Retorna uma lista de tuplas no mesmo
    formato de 'buscar_produto_por_ean': (id, cod_ean, nome, preco, quantidade).
    """
    try:
        termo = str(termo_busca).strip()
        if not termo:
            return []

        # Usamos .or_() para localizar o termo tanto no código de barras quanto no nome
        # em uma única viagem ao banco, sem precisar disparar duas queries separadas
        filtro_or = f"cod_ean.ilike.%{termo}%,nome.ilike.%{termo}%"

        response = supabase_client.table("produtos")\
            .select("id, cod_ean, nome, preco, quantidade")\
            .eq("ativo", True)\
            .or_(filtro_or)\
            .order("nome", desc=False)\
            .limit(limite)\
            .execute()

        dados = response.data if response.data else []

        # Devolvemos os dados formatados em tupla para manter compatibilidade com a UI do PDV
        lista_tuplas = []
        for item in dados:
            lista_tuplas.append((
                item.get("id"),
                item.get("cod_ean"),
                item.get("nome"),
                float(item.get("preco", 0.0)),
                int(item.get("quantidade", 0))
            ))
        return lista_tuplas

    except Exception as e:
        print(f"❌ ERRO AO PESQUISAR PRODUTOS NO SUPABASE (PDV): {e}")
        return []


def salvar_venda(id_operador, valor_total, lista_itens=None, status='CONCLUIDA'):
    """
    Função híbrida para o Supabase: 
    - Se status='CONCLUIDA': Salva venda, insere itens em lote e baixa estoque de cada um.
    - Se status='CANCELADA': Salva apenas o cabeçalho da venda para auditoria de caixa.
    """
    try:
        # 1. SALVA O CABEÇALHO DA VENDA
        payload_venda = {
            "id_operador": int(id_operador),
            "valor_total": float(valor_total),
            "status": status
        }
        
        response_venda = supabase_client.table("vendas").insert(payload_venda).execute()
        
        if not response_venda.data:
            return False, "Não foi possível registrar o cabeçalho da venda."
            
        id_venda = response_venda.data[0].get("id")

        # 2. LÓGICA CONDICIONAL: Só processa itens e estoque se for CONCLUÍDA
        if status == 'CONCLUIDA' and lista_itens:
            payload_itens = []
            
            # Montamos o lote de itens para mandar tudo em uma única viagem de rede
            for item in lista_itens:
                payload_itens.append({
                    "id_venda": int(id_venda),
                    "id_produto": int(item['id']),
                    "quantidade": int(item['qtd']),
                    "preco_unitario": float(item['preco']),
                    "subtotal": float(item['subtotal'])
                })
                
                # 📉 BAIXA FÍSICA NO ESTOQUE:
                # Primeiro pegamos a quantidade atual que está na nuvem
                prod_atual = supabase_client.table("produtos").select("quantidade").eq("id", item['id']).execute()
                if prod_atual.data:
                    qtd_antiga = int(prod_atual.data[0].get("quantidade", 0))
                    nova_qtd = qtd_antiga - int(item['qtd'])
                    
                    # Atualizamos a nova quantidade direto na tabela produtos
                    supabase_client.table("produtos").update({"quantidade": nova_qtd}).eq("id", item['id']).execute()

            # Dispara a inserção em lote de todos os itens da venda de uma vez só!
            supabase_client.table("itens_venda").insert(payload_itens).execute()

        # 3. REGISTRA LOG DE AUDITORIA GERAL
        try:
            registrar_log(
                cursor=None,
                acao=f"VENDA_{status}",
                tabela="vendas",
                registro_id=id_venda,
                detalhes=f"Operador ID {id_operador} finalizou venda no valor de R$ {valor_total:.2f} como {status}."
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao gerar log da venda: {log_err}")

        return True, id_venda

    except Exception as e:
        print(f"❌ Erro crítico ao salvar venda no Supabase: {e}")
        return False, str(e)