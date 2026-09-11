from utils.auth import supabase_client


def relatorio_vendas_periodo(data_inicio, data_fim):
    """
    Relatório de Vendas por Período: total vendido, nº de vendas, ticket médio,
    breakdown por forma de pagamento e a lista detalhada de vendas CONCLUIDA
    dentro do intervalo [data_inicio, data_fim] (strings ISO 'aaaa-mm-dd').
    Vendas DEVOLVIDA/CANCELADA nunca entram aqui, propositalmente.
    """
    try:
        response = supabase_client.table("vendas")\
            .select("id, valor_total, data_venda, hora_venda, id_forma_pagamento, id_operador")\
            .eq("status", "CONCLUIDA")\
            .gte("data_venda", data_inicio)\
            .lte("data_venda", data_fim)\
            .order("data_venda", desc=True)\
            .order("hora_venda", desc=True)\
            .execute()

        vendas = response.data or []

        total_vendido = sum(float(v.get("valor_total", 0)) for v in vendas)
        num_vendas = len(vendas)
        ticket_medio = total_vendido / num_vendas if num_vendas else 0.0

        totais_forma = {}
        for v in vendas:
            forma = v.get("id_forma_pagamento")
            totais_forma[forma] = totais_forma.get(forma, 0.0) + float(v.get("valor_total", 0))

        # Resolve nomes de operador à parte (vendas.id_operador não tem FK formal pra login)
        ids_operadores = list({v.get("id_operador") for v in vendas if v.get("id_operador")})
        mapa_nomes = {}
        if ids_operadores:
            operadores_resp = supabase_client.table("login").select("id, nome").in_("id", ids_operadores).execute()
            mapa_nomes = {op["id"]: op["nome"] for op in (operadores_resp.data or [])}

        lista_vendas = []
        for v in vendas:
            lista_vendas.append((
                v.get("id"),
                mapa_nomes.get(v.get("id_operador"), "—"),
                float(v.get("valor_total", 0)),
                v.get("data_venda"),
                v.get("hora_venda"),
                v.get("id_forma_pagamento")
            ))

        return {
            "total_vendido": total_vendido,
            "num_vendas": num_vendas,
            "ticket_medio": ticket_medio,
            "totais_forma": totais_forma,
            "vendas": lista_vendas
        }

    except Exception as e:
        print(f"❌ Erro ao gerar relatório de vendas por período no Supabase: {e}")
        return None


def relatorio_compras_periodo(data_inicio, data_fim):
    """
    Relatório de Compras por Período: lista os pedidos de compra criados no
    intervalo (qualquer status), com total pedido, total recebido e contagem
    de pedidos por status.
    """
    try:
        response = supabase_client.table("pedidos_compra")\
            .select("id, status, valor_total, valor_recebido, criado_em, id_fornecedor, fornecedores(nome_fantasia)")\
            .gte("criado_em", f"{data_inicio}T00:00:00")\
            .lte("criado_em", f"{data_fim}T23:59:59")\
            .order("criado_em", desc=True)\
            .execute()

        pedidos = response.data or []

        total_pedido = sum(float(p.get("valor_total", 0)) for p in pedidos)
        total_recebido = sum(float(p.get("valor_recebido") or 0) for p in pedidos if p.get("valor_recebido") is not None)

        contagem_status = {"PENDENTE": 0, "RECEBIDO": 0, "CANCELADO": 0}
        for p in pedidos:
            status = p.get("status")
            if status in contagem_status:
                contagem_status[status] += 1

        lista_pedidos = []
        for p in pedidos:
            nome_fornecedor = (p.get("fornecedores") or {}).get("nome_fantasia", "—")
            valor_recebido = p.get("valor_recebido")
            lista_pedidos.append((
                p.get("id"),
                nome_fornecedor,
                p.get("status"),
                float(p.get("valor_total", 0)),
                float(valor_recebido) if valor_recebido is not None else None,
                p.get("criado_em")
            ))

        return {
            "total_pedido": total_pedido,
            "total_recebido": total_recebido,
            "contagem_status": contagem_status,
            "pedidos": lista_pedidos
        }

    except Exception as e:
        print(f"❌ Erro ao gerar relatório de compras por período no Supabase: {e}")
        return None


def relatorio_divergencia_compras(data_inicio, data_fim):
    """
    Relatório de Divergência de Compras: para os pedidos RECEBIDO criados no
    período, compara quantidade pedida x recebida, item a item, e agrega o
    total de unidades faltantes (ou excedentes) por pedido. Pedidos sem
    nenhuma divergência não aparecem na lista.
    """
    try:
        pedidos_resp = supabase_client.table("pedidos_compra")\
            .select("id, criado_em, id_fornecedor, fornecedores(nome_fantasia)")\
            .eq("status", "RECEBIDO")\
            .gte("criado_em", f"{data_inicio}T00:00:00")\
            .lte("criado_em", f"{data_fim}T23:59:59")\
            .execute()

        pedidos = pedidos_resp.data or []
        resultado_pedidos = []
        total_faltante_geral = 0
        total_excedente_geral = 0

        for pedido in pedidos:
            id_pedido = pedido.get("id")
            nome_fornecedor = (pedido.get("fornecedores") or {}).get("nome_fantasia", "—")

            itens_resp = supabase_client.table("itens_pedido_compra")\
                .select("quantidade_pedida, quantidade_recebida, produtos(nome)")\
                .eq("id_pedido", id_pedido)\
                .execute()

            divergencias_pedido = []
            for item in (itens_resp.data or []):
                qtd_pedida = item.get("quantidade_pedida") or 0
                qtd_recebida = item.get("quantidade_recebida")
                if qtd_recebida is None:
                    continue

                diferenca = qtd_pedida - qtd_recebida
                if diferenca != 0:
                    nome_produto = (item.get("produtos") or {}).get("nome", "Produto removido")
                    divergencias_pedido.append((nome_produto, qtd_pedida, qtd_recebida, diferenca))
                    if diferenca > 0:
                        total_faltante_geral += diferenca
                    else:
                        total_excedente_geral += abs(diferenca)

            if divergencias_pedido:
                resultado_pedidos.append({
                    "id_pedido": id_pedido,
                    "nome_fornecedor": nome_fornecedor,
                    "criado_em": pedido.get("criado_em"),
                    "itens": divergencias_pedido
                })

        return {
            "pedidos": resultado_pedidos,
            "total_faltante": total_faltante_geral,
            "total_excedente": total_excedente_geral
        }

    except Exception as e:
        print(f"❌ Erro ao gerar relatório de divergência de compras no Supabase: {e}")
        return None


def relatorio_dre_simplificado(data_inicio, data_fim):
    """
    DRE Simplificado: Receita - CMV - Despesas = Lucro, no período informado
    (strings ISO 'aaaa-mm-dd').

    Receita = soma das vendas CONCLUIDA no período (por data_venda).
    CMV = soma de (quantidade vendida x preco_custo ATUAL do produto). É uma
    APROXIMAÇÃO: itens_venda não guarda o custo do produto na época da venda,
    só o preço de venda — então o CMV de um período passado usa o custo de
    HOJE, que pode já ter mudado desde então via Pedidos de Compra.
    Despesas = soma dos títulos financeiros tipo PAGAR já com status PAGO,
    filtrando por data_pagamento (regime de caixa, não de competência).
    """
    try:
        vendas_resp = supabase_client.table("vendas")\
            .select("id, valor_total")\
            .eq("status", "CONCLUIDA")\
            .gte("data_venda", data_inicio)\
            .lte("data_venda", data_fim)\
            .execute()

        vendas = vendas_resp.data or []
        receita = sum(float(v.get("valor_total", 0)) for v in vendas)
        ids_vendas = [v["id"] for v in vendas]

        cmv = 0.0
        if ids_vendas:
            itens_resp = supabase_client.table("itens_venda")\
                .select("id_produto, quantidade")\
                .in_("id_venda", ids_vendas)\
                .execute()

            itens = itens_resp.data or []
            ids_produtos = list({i["id_produto"] for i in itens if i.get("id_produto")})

            mapa_custos = {}
            if ids_produtos:
                produtos_resp = supabase_client.table("produtos").select("id, preco_custo").in_("id", ids_produtos).execute()
                mapa_custos = {p["id"]: float(p.get("preco_custo") or 0) for p in (produtos_resp.data or [])}

            for item in itens:
                custo_unitario = mapa_custos.get(item.get("id_produto"), 0.0)
                cmv += float(item.get("quantidade", 0)) * custo_unitario

        despesas_resp = supabase_client.table("financeiro_titulos")\
            .select("valor")\
            .eq("tipo", "PAGAR")\
            .eq("status", "PAGO")\
            .gte("data_pagamento", f"{data_inicio}T00:00:00")\
            .lte("data_pagamento", f"{data_fim}T23:59:59")\
            .execute()

        despesas = sum(float(d.get("valor", 0)) for d in (despesas_resp.data or []))

        lucro = receita - cmv - despesas

        return {
            "receita": receita,
            "cmv": cmv,
            "despesas": despesas,
            "lucro": lucro
        }

    except Exception as e:
        print(f"❌ Erro ao gerar DRE simplificado no Supabase: {e}")
        return None
