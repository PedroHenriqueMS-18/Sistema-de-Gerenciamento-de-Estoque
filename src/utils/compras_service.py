from datetime import datetime, timezone
from utils.auth import supabase_client, UsuarioSessao
from utils.logger import registrar_log
from utils.financeiro_service import criar_titulo_financeiro, cancelar_titulo_financeiro, ajustar_valor_titulo, formatar_moeda_br


def buscar_pedidos_compra(status_filtro="TODOS", termo_busca=""):
    """
    Lista os pedidos de compra do Supabase, mais recentes primeiro, com o nome do
    fornecedor já resolvido via join. Filtra por status e/ou nome do fornecedor.
    """
    try:
        query = supabase_client.table("pedidos_compra")\
            .select("id, status, valor_total, valor_recebido, criado_em, id_fornecedor, fornecedores(nome_fantasia)")

        if status_filtro and status_filtro != "TODOS":
            query = query.eq("status", status_filtro)

        response = query.order("criado_em", desc=True).execute()
        dados = response.data or []

        if termo_busca:
            termo_lower = termo_busca.lower()
            dados = [d for d in dados if termo_lower in (d.get("fornecedores") or {}).get("nome_fantasia", "").lower()]

        resultado = []
        for item in dados:
            nome_fornecedor = (item.get("fornecedores") or {}).get("nome_fantasia", "—")
            valor_recebido = item.get("valor_recebido")
            resultado.append((
                item.get("id"),
                nome_fornecedor,
                item.get("status"),
                float(item.get("valor_total", 0)),
                float(valor_recebido) if valor_recebido is not None else None,
                item.get("criado_em")
            ))
        return resultado

    except Exception as e:
        print(f"❌ Erro ao buscar pedidos de compra no Supabase: {e}")
        return []


def buscar_itens_pedido(id_pedido):
    """Lista os itens de um pedido de compra específico, com o nome do produto resolvido via join."""
    try:
        response = supabase_client.table("itens_pedido_compra")\
            .select("id, id_produto, quantidade_pedida, quantidade_recebida, custo_unitario, produtos(nome)")\
            .eq("id_pedido", int(id_pedido))\
            .execute()

        resultado = []
        for item in (response.data or []):
            nome_produto = (item.get("produtos") or {}).get("nome", "Produto removido")
            resultado.append((
                item.get("id"),
                item.get("id_produto"),
                nome_produto,
                item.get("quantidade_pedida"),
                item.get("quantidade_recebida"),
                float(item.get("custo_unitario", 0))
            ))
        return resultado

    except Exception as e:
        print(f"❌ Erro ao buscar itens do pedido de compra no Supabase: {e}")
        return []


def criar_pedido_compra(id_fornecedor, itens, vencimento_pagamento, observacao=""):
    """
    Cria um novo pedido de compra (status PENDENTE) com seus itens, e já gera
    automaticamente a conta a pagar correspondente no Financeiro, vinculando o
    título ao pedido. 'itens' é uma lista de dicts com id_produto, quantidade e
    custo_unitario. O valor do pedido = soma de (quantidade × custo_unitario).
    """
    try:
        valor_total = sum(float(item["quantidade"]) * float(item["custo_unitario"]) for item in itens)

        payload_pedido = {
            "id_fornecedor": int(id_fornecedor),
            "id_operador": UsuarioSessao.id,
            "status": "PENDENTE",
            "valor_total": valor_total,
            "observacao": observacao.strip() if observacao else None
        }

        resp_pedido = supabase_client.table("pedidos_compra").insert(payload_pedido).execute()
        if not resp_pedido.data:
            return False, "Não foi possível criar o pedido de compra."

        id_pedido = resp_pedido.data[0].get("id")

        payload_itens = [{
            "id_pedido": id_pedido,
            "id_produto": int(item["id_produto"]),
            "quantidade_pedida": int(item["quantidade"]),
            "custo_unitario": float(item["custo_unitario"])
        } for item in itens]

        supabase_client.table("itens_pedido_compra").insert(payload_itens).execute()

        # Busca o nome do fornecedor só pra deixar a descrição da conta a pagar legível
        fornecedor_resp = supabase_client.table("fornecedores").select("nome_fantasia").eq("id", int(id_fornecedor)).execute()
        nome_fornecedor = fornecedor_resp.data[0].get("nome_fantasia") if fornecedor_resp.data else "Fornecedor"

        # --- GERA A CONTA A PAGAR AUTOMATICAMENTE, JÁ VINCULADA AO PEDIDO ---
        dados_titulo = {
            "tipo": "PAGAR",
            "descricao": f"Pedido de Compra #{id_pedido} - {nome_fornecedor}",
            "categoria": "Fornecedor",
            "valor": valor_total,
            "vencimento": vencimento_pagamento,
            "id_fornecedor": id_fornecedor,
            "observacao": observacao
        }
        sucesso_titulo, resultado_titulo = criar_titulo_financeiro(dados_titulo)

        if sucesso_titulo:
            supabase_client.table("pedidos_compra").update({"id_titulo_financeiro": resultado_titulo}).eq("id", id_pedido).execute()
        else:
            print(f"⚠️ Pedido #{id_pedido} criado, mas não foi possível gerar a conta a pagar: {resultado_titulo}")

        try:
            registrar_log(
                acao="PEDIDO_COMPRA_CRIADO",
                tabela="pedidos_compra",
                registro_id=id_pedido,
                detalhes=f"{UsuarioSessao.nome} criou o pedido de compra #{id_pedido} para {nome_fornecedor}, "
                         f"valor {formatar_moeda_br(valor_total)}."
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao gerar log do pedido de compra: {log_err}")

        return True, id_pedido

    except Exception as e:
        print(f"❌ Erro ao criar pedido de compra no Supabase: {e}")
        return False, str(e)


def confirmar_recebimento_pedido(id_pedido, itens_recebidos):
    """
    Confirma o recebimento de um pedido PENDENTE. 'itens_recebidos' é uma lista de
    dicts com id_item, id_produto, nome_produto, quantidade_pedida, quantidade_recebida
    e custo_unitario. Para cada item: dá entrada no estoque com a quantidade
    REALMENTE recebida (não a pedida) e sobrescreve o preco_custo do produto pelo
    último valor informado.

    O valor final da compra é recalculado com base no que realmente chegou — mesmo
    custo unitário, só a quantidade muda (quantidade_recebida × custo_unitario, somado
    por item) — pois é isso que reflete o boleto real do fornecedor. Esse valor fica
    salvo em 'valor_recebido' (o 'valor_total' original do pedido não é apagado, serve
    de referência pra divergência). Se esse valor recalculado for diferente do valor
    originalmente cobrado, a conta a pagar vinculada no Financeiro é ajustada — só se
    ainda estiver PENDENTE (uma conta já paga ou cancelada nunca é sobrescrita).

    Retorna (True, resumo) em sucesso — 'resumo' é um dict com 'divergencias' (lista de
    itens onde pedido ≠ recebido), 'valor_pedido', 'valor_recebido' e 'ajuste_titulo'
    (None se não precisou ajustar, ou uma mensagem quando não foi possível ajustar).
    """
    try:
        pedido_resp = supabase_client.table("pedidos_compra").select("valor_total, id_titulo_financeiro").eq("id", int(id_pedido)).execute()
        if not pedido_resp.data:
            return False, "Pedido não encontrado."

        valor_pedido_original = float(pedido_resp.data[0].get("valor_total", 0))
        id_titulo_financeiro = pedido_resp.data[0].get("id_titulo_financeiro")

        divergencias = []
        valor_recebido = 0.0

        for item in itens_recebidos:
            qtd_recebida = int(item["quantidade_recebida"])
            qtd_pedida = int(item["quantidade_pedida"])
            custo = float(item["custo_unitario"])  # custo unitário NUNCA muda no recebimento

            valor_recebido += qtd_recebida * custo

            if qtd_recebida != qtd_pedida:
                divergencias.append({
                    "nome_produto": item["nome_produto"],
                    "quantidade_pedida": qtd_pedida,
                    "quantidade_recebida": qtd_recebida,
                    "diferenca": qtd_pedida - qtd_recebida
                })

            # Dá entrada no estoque (soma sobre o valor atual) e sobrescreve o custo do produto
            produto_resp = supabase_client.table("produtos").select("quantidade").eq("id", int(item["id_produto"])).execute()
            estoque_atual = produto_resp.data[0].get("quantidade", 0) if produto_resp.data else 0

            supabase_client.table("produtos").update({
                "quantidade": estoque_atual + qtd_recebida,
                "preco_custo": custo
            }).eq("id", int(item["id_produto"])).execute()

            supabase_client.table("itens_pedido_compra").update({
                "quantidade_recebida": qtd_recebida
            }).eq("id", int(item["id_item"])).execute()

        supabase_client.table("pedidos_compra").update({
            "status": "RECEBIDO",
            "data_recebimento": datetime.now(timezone.utc).isoformat(),
            "valor_recebido": valor_recebido
        }).eq("id", int(id_pedido)).execute()

        # --- AJUSTA A CONTA A PAGAR PRO VALOR REALMENTE RECEBIDO, SE FOR DIFERENTE ---
        ajuste_titulo = None
        if id_titulo_financeiro and abs(valor_recebido - valor_pedido_original) > 0.004:
            sucesso_ajuste, motivo_ajuste = ajustar_valor_titulo(id_titulo_financeiro, valor_recebido)
            if not sucesso_ajuste:
                ajuste_titulo = motivo_ajuste  # ex: "já foi baixado" — divergência fica só registrada, sem travar o fluxo

        try:
            resumo_log = f"Divergências em {len(divergencias)} item(ns)." if divergencias else "Sem divergências."
            registrar_log(
                acao="PEDIDO_COMPRA_RECEBIDO",
                tabela="pedidos_compra",
                registro_id=id_pedido,
                detalhes=f"{UsuarioSessao.nome} confirmou o recebimento do pedido #{id_pedido}. {resumo_log} "
                         f"Valor pedido: {formatar_moeda_br(valor_pedido_original)}, valor recebido: {formatar_moeda_br(valor_recebido)}."
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao gerar log de recebimento do pedido de compra: {log_err}")

        return True, {
            "divergencias": divergencias,
            "valor_pedido": valor_pedido_original,
            "valor_recebido": valor_recebido,
            "ajuste_titulo": ajuste_titulo
        }

    except Exception as e:
        print(f"❌ Erro ao confirmar recebimento do pedido de compra no Supabase: {e}")
        return False, str(e)


def cancelar_pedido_compra(id_pedido):
    """
    Cancela um pedido de compra em qualquer status. Se já estava RECEBIDO, estorna do
    estoque as quantidades que tinham entrado (sem deixar o estoque negativo). Também
    cancela a conta a pagar vinculada no Financeiro, se existir.
    """
    try:
        pedido_resp = supabase_client.table("pedidos_compra").select("status, id_titulo_financeiro").eq("id", int(id_pedido)).execute()
        if not pedido_resp.data:
            return False, "Pedido não encontrado."

        pedido = pedido_resp.data[0]

        if pedido.get("status") == "RECEBIDO":
            itens_resp = supabase_client.table("itens_pedido_compra")\
                .select("id_produto, quantidade_recebida")\
                .eq("id_pedido", int(id_pedido))\
                .execute()

            for item in (itens_resp.data or []):
                qtd_recebida = item.get("quantidade_recebida") or 0
                if qtd_recebida <= 0:
                    continue

                produto_resp = supabase_client.table("produtos").select("quantidade").eq("id", item["id_produto"]).execute()
                estoque_atual = produto_resp.data[0].get("quantidade", 0) if produto_resp.data else 0
                novo_estoque = max(0, estoque_atual - qtd_recebida)

                supabase_client.table("produtos").update({"quantidade": novo_estoque}).eq("id", item["id_produto"]).execute()

        supabase_client.table("pedidos_compra").update({"status": "CANCELADO"}).eq("id", int(id_pedido)).execute()

        if pedido.get("id_titulo_financeiro"):
            cancelar_titulo_financeiro(pedido["id_titulo_financeiro"], "PAGAR")

        try:
            registrar_log(
                acao="PEDIDO_COMPRA_CANCELADO",
                tabela="pedidos_compra",
                registro_id=id_pedido,
                detalhes=f"{UsuarioSessao.nome} cancelou o pedido de compra #{id_pedido} (estava {pedido.get('status')})."
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao gerar log de cancelamento do pedido de compra: {log_err}")

        return True, None

    except Exception as e:
        print(f"❌ Erro ao cancelar pedido de compra no Supabase: {e}")
        return False, str(e)
