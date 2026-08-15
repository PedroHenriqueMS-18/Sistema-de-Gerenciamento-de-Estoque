import os
import sys
import subprocess
from datetime import datetime, timezone
from utils.auth import supabase_client
from utils.logger import registrar_log


def formatar_moeda_br(valor):
    """Formata um número no padrão monetário brasileiro, com separador de milhar (R$ 1.234,56)."""
    texto = f"{float(valor):,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def formatar_data_br(valor_iso):
    """Converte um timestamp ISO do Supabase (UTC) para 'dd/mm/aaaa HH:MM:SS' no horário local da máquina."""
    try:
        texto = str(valor_iso).replace("Z", "+00:00")
        momento_local = datetime.fromisoformat(texto).astimezone()
        return momento_local.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(valor_iso)


def abrir_arquivo(caminho):
    """Abre um arquivo no programa padrão do sistema operacional (usado para o comprovante)."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(caminho)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", caminho])
        else:
            subprocess.Popen(["xdg-open", caminho])
        return True
    except Exception as e:
        print(f"⚠️ Não foi possível abrir o comprovante automaticamente: {e}")
        return False


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


def salvar_venda(id_operador, valor_total, id_caixa=None, lista_itens=None, status='CONCLUIDA', id_forma_pagamento=None, troco=0.0):
    """
    Função híbrida para o Supabase: 
    - Se status='CONCLUIDA': Salva venda, insere itens em lote e baixa estoque de cada um.
    - Se status='CANCELADA': Salva apenas o cabeçalho da venda para auditoria de caixa.
    'id_caixa' vincula a venda à sessão de caixa aberta (tabela sessoes_caixa), permitindo
    calcular quanto dinheiro físico entrou na gaveta durante o expediente (uso na Sangria).
    """
    try:
        # 1. SALVA O CABEÇALHO DA VENDA
        payload_venda = {
            "id_operador": int(id_operador),
            "valor_total": float(valor_total),
            "status": status
        }

        if id_caixa is not None:
            payload_venda["id_caixa"] = int(id_caixa)
        if id_forma_pagamento is not None:
            payload_venda["id_forma_pagamento"] = int(id_forma_pagamento)
        if troco:
            payload_venda["troco"] = float(troco)
        
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


def abrir_sessao_caixa(id_operador, valor_abertura):
    """
    Registra a abertura do caixa no Supabase (tabela sessoes_caixa) e devolve a linha
    inserida (id, data_abertura, etc). Esse id passa a identificar a sessão em todas as
    movimentações seguintes (vendas, sangrias e suprimentos) até o fechamento do caixa.
    Retorna None em caso de falha.
    """
    try:
        payload = {
            "id_operador": int(id_operador),
            "valor_abertura": float(valor_abertura),
            "status": "ABERTO"
        }

        response = supabase_client.table("sessoes_caixa").insert(payload).execute()

        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        print(f"❌ Erro ao abrir sessão de caixa no Supabase: {e}")
        return None


def fechar_sessao_caixa(id_caixa, valor_fechamento, observacao=None):
    """
    Marca a sessão de caixa como FECHADA, registrando o valor efetivamente contado
    na gaveta (declarado pelo operador) e o horário de encerramento do turno.
    """
    try:
        payload = {
            "status": "FECHADO",
            "valor_fechamento": float(valor_fechamento),
            "data_fechamento": datetime.now(timezone.utc).isoformat()
        }
        if observacao:
            payload["observacao"] = observacao.strip()

        response = supabase_client.table("sessoes_caixa").update(payload).eq("id", int(id_caixa)).execute()

        if response.data:
            return True, response.data[0]
        return False, "Não foi possível atualizar a sessão de caixa."

    except Exception as e:
        print(f"❌ Erro ao fechar sessão de caixa no Supabase: {e}")
        return False, str(e)


def _obter_componentes_caixa(id_caixa):
    """
    Função interna: busca os valores brutos usados no cálculo do dinheiro físico da
    gaveta (vendas em dinheiro, suprimentos e sangrias) dentro de uma sessão de caixa.
    Compartilhada por 'calcular_saldo_caixa' (Sangria) e 'montar_resumo_fechamento_caixa'
    (Fechamento) para não duplicar as mesmas consultas.
    """
    vendas_dinheiro_resp = supabase_client.table("vendas")\
        .select("valor_total")\
        .eq("id_caixa", int(id_caixa))\
        .eq("status", "CONCLUIDA")\
        .eq("id_forma_pagamento", 1)\
        .execute()
    total_vendas_dinheiro = sum(float(v.get("valor_total", 0)) for v in (vendas_dinheiro_resp.data or []))

    movimentacoes_resp = supabase_client.table("movimentacoes_caixa")\
        .select("tipo, valor")\
        .eq("id_caixa", int(id_caixa))\
        .execute()
    total_suprimentos = sum(float(m.get("valor", 0)) for m in (movimentacoes_resp.data or []) if m.get("tipo") == "SUPRIMENTO")
    total_sangrias = sum(float(m.get("valor", 0)) for m in (movimentacoes_resp.data or []) if m.get("tipo") == "SANGRIA")

    return total_vendas_dinheiro, total_suprimentos, total_sangrias


def calcular_saldo_caixa(id_caixa, valor_abertura):
    """
    Calcula o dinheiro físico disponível na gaveta para fins de Sangria:

        Dinheiro em Gaveta = Saldo Abertura + Vendas em Dinheiro
                              + Suprimentos - Sangrias Anteriores

    ⚠️ Regra de Ouro: vendas em Cartão de Crédito/Débito ou PIX (id_forma_pagamento
    diferente de 1) NÃO entram nesse cálculo, pois esse dinheiro nunca passa pela gaveta.
    """
    try:
        total_vendas_dinheiro, total_suprimentos, total_sangrias = _obter_componentes_caixa(id_caixa)
        return float(valor_abertura) + total_vendas_dinheiro + total_suprimentos - total_sangrias

    except Exception as e:
        print(f"❌ Erro ao calcular saldo do caixa no Supabase: {e}")
        return 0.0


def calcular_totais_por_forma_pagamento(id_caixa):
    """
    Soma o valor total vendido (status='CONCLUIDA') em cada forma de pagamento dentro
    da sessão de caixa informada. Chave = id_forma_pagamento, valor = total vendido.
    Usado no espelho de Fechamento de Caixa para detalhar Cartão de Crédito, Cartão
    de Débito e PIX (o dinheiro é conciliado à parte, na conferência física da gaveta).
    """
    try:
        response = supabase_client.table("vendas")\
            .select("valor_total, id_forma_pagamento")\
            .eq("id_caixa", int(id_caixa))\
            .eq("status", "CONCLUIDA")\
            .execute()

        totais = {}
        for venda in (response.data or []):
            forma = venda.get("id_forma_pagamento")
            valor = float(venda.get("valor_total", 0))
            totais[forma] = totais.get(forma, 0.0) + valor

        return totais

    except Exception as e:
        print(f"❌ Erro ao calcular totais por forma de pagamento no Supabase: {e}")
        return {}


def montar_resumo_fechamento_caixa(id_caixa, valor_abertura):
    """
    Monta o resumo completo usado no espelho de Fechamento de Caixa: a quebra
    detalhada da conciliação em dinheiro (troco inicial, vendas em dinheiro,
    suprimentos, sangrias) e o total vendido em cada forma eletrônica (cartões
    e PIX), para conferência do operador/gerente. Retorna None em caso de falha.
    """
    try:
        total_vendas_dinheiro, total_suprimentos, total_sangrias = _obter_componentes_caixa(id_caixa)
        saldo_esperado = float(valor_abertura) + total_vendas_dinheiro + total_suprimentos - total_sangrias

        totais_formas = calcular_totais_por_forma_pagamento(id_caixa)

        return {
            "troco_abertura": float(valor_abertura),
            "vendas_dinheiro": total_vendas_dinheiro,
            "suprimentos": total_suprimentos,
            "sangrias": total_sangrias,
            "saldo_esperado": saldo_esperado,
            "cartao_credito": totais_formas.get(2, 0.0),
            "cartao_debito": totais_formas.get(3, 0.0),
            "pix": totais_formas.get(4, 0.0),
            "total_geral_vendido": sum(totais_formas.values())
        }

    except Exception as e:
        print(f"❌ Erro ao montar resumo de fechamento de caixa: {e}")
        return None


def registrar_movimentacao_caixa(id_caixa, id_operador, tipo, valor, observacao=""):
    """
    Registra uma Sangria ou Suprimento na tabela movimentacoes_caixa.
    'tipo' deve ser 'SANGRIA' ou 'SUPRIMENTO'. Retorna (True, id_movimentacao)
    em caso de sucesso, ou (False, mensagem_erro) em caso de falha.
    """
    try:
        payload = {
            "id_caixa": int(id_caixa),
            "id_operador": int(id_operador),
            "tipo": tipo,
            "valor": float(valor),
            "observacao": observacao.strip() if observacao else None
        }

        response = supabase_client.table("movimentacoes_caixa").insert(payload).execute()

        if not response.data:
            return False, "Não foi possível registrar a movimentação de caixa."

        id_movimentacao = response.data[0].get("id")

        try:
            registrar_log(
                acao=tipo,
                tabela="movimentacoes_caixa",
                registro_id=id_movimentacao,
                detalhes=f"Operador ID {id_operador} registrou {tipo} de R$ {float(valor):.2f} no caixa #{id_caixa}. Obs: {observacao}"
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao gerar log da movimentação de caixa: {log_err}")

        return True, id_movimentacao

    except Exception as e:
        print(f"❌ Erro crítico ao registrar movimentação de caixa no Supabase: {e}")
        return False, str(e)


def gerar_comprovante_sangria(id_movimentacao, id_caixa, operador_nome, valor, observacao, saldo_antes, saldo_depois):
    """
    Gera o comprovante de sangria em um arquivo .txt, no formato compacto de
    impressora térmica (~40 colunas). O operador deve imprimir/anexar esse
    comprovante físico na gaveta, comprovando a retirada até o fechamento do caixa.
    Retorna o caminho do arquivo gerado, ou None em caso de falha.
    """
    try:
        pasta_comprovantes = os.path.join(os.path.dirname(os.path.dirname(__file__)), "comprovantes")
        os.makedirs(pasta_comprovantes, exist_ok=True)

        agora = datetime.now()
        nome_arquivo = f"sangria_{id_movimentacao}_{agora.strftime('%Y%m%d_%H%M%S')}.txt"
        caminho_completo = os.path.join(pasta_comprovantes, nome_arquivo)

        linhas = [
            "=" * 40,
            "COMPROVANTE DE SANGRIA".center(40),
            "=" * 40,
            f"Data/Hora: {agora.strftime('%d/%m/%Y %H:%M:%S')}",
            f"Operador : {operador_nome}",
            f"Caixa    : #{id_caixa}",
            f"Mov. Num.: #{id_movimentacao}",
            "-" * 40,
            f"VALOR RETIRADO: R$ {valor:.2f}".replace('.', ','),
            "",
            "Motivo:",
            observacao or "(sem observação)",
            "-" * 40,
            f"Saldo em gaveta antes : R$ {saldo_antes:.2f}".replace('.', ','),
            f"Saldo em gaveta depois: R$ {saldo_depois:.2f}".replace('.', ','),
            "=" * 40,
            "",
            "Assinatura do operador:",
            "_" * 30,
            "=" * 40,
        ]

        with open(caminho_completo, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas))

        return caminho_completo

    except Exception as e:
        print(f"❌ Erro ao gerar comprovante de sangria: {e}")
        return None


def gerar_comprovante_fechamento(id_caixa, operador_nome, data_abertura, resumo, valor_declarado, diferenca, observacao=""):
    """
    Gera o espelho de Fechamento de Caixa em .txt, no formato compacto de impressora
    térmica (~40 colunas), com a conciliação do dinheiro físico e o total vendido em
    cada forma de pagamento. Retorna o caminho do arquivo gerado, ou None em falha.
    """
    try:
        pasta_comprovantes = os.path.join(os.path.dirname(os.path.dirname(__file__)), "comprovantes")
        os.makedirs(pasta_comprovantes, exist_ok=True)

        agora = datetime.now()
        nome_arquivo = f"fechamento_{id_caixa}_{agora.strftime('%Y%m%d_%H%M%S')}.txt"
        caminho_completo = os.path.join(pasta_comprovantes, nome_arquivo)

        # Tolerância de meio centavo para arredondamento de ponto flutuante
        if diferenca > 0.004:
            rotulo_diferenca, sinal = "DIFERENÇA (SOBRA)", "+"
        elif diferenca < -0.004:
            rotulo_diferenca, sinal = "DIFERENÇA (QUEBRA)", "-"
        else:
            rotulo_diferenca, sinal = "DIFERENÇA (CONFERE)", ""

        linhas = [
            "=" * 40,
            "FECHAMENTO DE CAIXA".center(40),
            "=" * 40,
            f"{'Sessão Caixa'.ljust(13)}: #{id_caixa}",
            f"{'Operador'.ljust(13)}: {operador_nome}",
            f"{'Data Abertura'.ljust(13)}: {formatar_data_br(data_abertura)}",
            f"{'Data Fecho'.ljust(13)}: {agora.strftime('%d/%m/%Y %H:%M:%S')}",
            "-" * 40,
            f"{'(+) Troco Inicial'.ljust(20)}: {formatar_moeda_br(resumo['troco_abertura'])}",
            f"{'(+) Vendas Dinheiro'.ljust(20)}: {formatar_moeda_br(resumo['vendas_dinheiro'])}",
            f"{'(+) Suprimentos'.ljust(20)}: {formatar_moeda_br(resumo['suprimentos'])}",
            f"{'(-) Sangrias'.ljust(20)}: {formatar_moeda_br(resumo['sangrias'])}",
            "-" * 40,
            f"{'(=) DINHEIRO ESPERADO'.ljust(23)}: {formatar_moeda_br(resumo['saldo_esperado'])}",
            f"{'(=) DINHEIRO DECLARADO'.ljust(23)}: {formatar_moeda_br(valor_declarado)}",
            "-" * 40,
            f"{rotulo_diferenca.ljust(23)}: {sinal}{formatar_moeda_br(abs(diferenca))}",
            "-" * 40,
            "OUTRAS FORMAS:",
            f"{'Cartão de Crédito'.ljust(20)}: {formatar_moeda_br(resumo['cartao_credito'])}",
            f"{'Cartão de Débito'.ljust(20)}: {formatar_moeda_br(resumo['cartao_debito'])}",
            f"{'PIX'.ljust(20)}: {formatar_moeda_br(resumo['pix'])}",
            f"{'TOTAL GERAL VENDIDO'.ljust(20)}: {formatar_moeda_br(resumo['total_geral_vendido'])}",
            "=" * 40,
        ]

        if observacao:
            linhas += ["Observação:", observacao, "=" * 40]

        linhas += [
            "Assinatura do Operador: ______________",
            "Assinatura do Gerente : ______________",
            "=" * 40,
        ]

        with open(caminho_completo, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas))

        return caminho_completo

    except Exception as e:
        print(f"❌ Erro ao gerar comprovante de fechamento: {e}")
        return None