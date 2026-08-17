from datetime import date, datetime, timezone
from utils.auth import supabase_client, UsuarioSessao
from utils.logger import registrar_log


def formatar_moeda_br(valor):
    """Formata um número no padrão monetário brasileiro (R$ 1.234,56)."""
    texto = f"{float(valor):,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def formatar_data_exibir(data_iso):
    """Converte uma data 'aaaa-mm-dd' (coluna DATE do Postgres) para 'dd/mm/aaaa'."""
    try:
        ano, mes, dia = str(data_iso).split("-")[:3]
        return f"{dia}/{mes}/{ano}"
    except Exception:
        return str(data_iso)


def buscar_titulos_financeiros(tipo, status_filtro="TODOS", termo_busca=""):
    """
    Lista os títulos financeiros (contas a pagar OU a receber, conforme 'tipo') do
    Supabase, ordenados por vencimento. Filtra por status e/ou por trecho da descrição.
    """
    try:
        query = supabase_client.table("financeiro_titulos")\
            .select("id, descricao, categoria, valor, vencimento, status, id_fornecedor")\
            .eq("tipo", tipo)

        if status_filtro and status_filtro != "TODOS":
            query = query.eq("status", status_filtro)

        if termo_busca:
            query = query.ilike("descricao", f"%{termo_busca}%")

        response = query.order("vencimento", desc=False).execute()

        dados_tupla = []
        for item in (response.data or []):
            dados_tupla.append((
                item.get("id"),
                item.get("descricao"),
                item.get("categoria"),
                float(item.get("valor", 0)),
                item.get("vencimento"),
                item.get("status"),
                item.get("id_fornecedor")
            ))
        return dados_tupla

    except Exception as e:
        print(f"❌ Erro ao buscar títulos financeiros no Supabase: {e}")
        return []


def calcular_totais_financeiros(tipo):
    """
    Calcula os totais usados nos cards de resumo da tela de Financeiro:
    total pendente, total já vencido (dentro do pendente) e total pago/recebido
    dentro do mês corrente.
    """
    try:
        hoje = date.today().isoformat()
        primeiro_dia_mes = date.today().replace(day=1).isoformat()

        pendentes_resp = supabase_client.table("financeiro_titulos")\
            .select("valor, vencimento")\
            .eq("tipo", tipo)\
            .eq("status", "PENDENTE")\
            .execute()

        total_pendente = 0.0
        total_vencido = 0.0
        for titulo in (pendentes_resp.data or []):
            valor = float(titulo.get("valor", 0))
            total_pendente += valor
            if str(titulo.get("vencimento")) < hoje:
                total_vencido += valor

        pagos_resp = supabase_client.table("financeiro_titulos")\
            .select("valor")\
            .eq("tipo", tipo)\
            .eq("status", "PAGO")\
            .gte("data_pagamento", primeiro_dia_mes)\
            .execute()

        total_pago_mes = sum(float(t.get("valor", 0)) for t in (pagos_resp.data or []))

        return {
            "total_pendente": total_pendente,
            "total_vencido": total_vencido,
            "total_pago_mes": total_pago_mes
        }

    except Exception as e:
        print(f"❌ Erro ao calcular totais financeiros no Supabase: {e}")
        return {"total_pendente": 0.0, "total_vencido": 0.0, "total_pago_mes": 0.0}


def criar_titulo_financeiro(dados):
    """
    Insere um novo título financeiro (conta a pagar ou a receber), sempre nascendo
    como 'PENDENTE', e gera o log de auditoria. 'dados' deve conter: tipo, descricao,
    categoria, valor, vencimento (ISO 'aaaa-mm-dd'), id_fornecedor (opcional), observacao.
    """
    try:
        payload = {
            "tipo": dados["tipo"],
            "descricao": dados["descricao"].strip(),
            "categoria": dados["categoria"],
            "valor": float(dados["valor"]),
            "vencimento": dados["vencimento"],
            "id_operador": UsuarioSessao.id,
            "status": "PENDENTE"
        }

        if dados.get("id_fornecedor"):
            payload["id_fornecedor"] = int(dados["id_fornecedor"])
        if dados.get("observacao"):
            payload["observacao"] = dados["observacao"].strip()

        response = supabase_client.table("financeiro_titulos").insert(payload).execute()

        novo_id = response.data[0].get("id") if response.data else None

        try:
            registrar_log(
                acao=f"LANCAMENTO_{dados['tipo']}",
                tabela="financeiro_titulos",
                registro_id=novo_id,
                detalhes=f"{UsuarioSessao.nome} lançou {dados['tipo']} '{dados['descricao']}' "
                         f"no valor de {formatar_moeda_br(dados['valor'])}, vencimento {formatar_data_exibir(dados['vencimento'])}."
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao gerar log do lançamento financeiro: {log_err}")

        return True, novo_id

    except Exception as e:
        print(f"❌ Erro ao cadastrar título financeiro no Supabase: {e}")
        return False, str(e)


def marcar_titulo_como_pago(id_titulo, tipo):
    """Dá baixa integral em um título (PENDENTE -> PAGO), registrando a data efetiva."""
    try:
        payload = {
            "status": "PAGO",
            "data_pagamento": datetime.now(timezone.utc).isoformat()
        }

        response = supabase_client.table("financeiro_titulos").update(payload).eq("id", int(id_titulo)).execute()

        if not response.data:
            return False

        try:
            registrar_log(
                acao=f"BAIXA_{tipo}",
                tabela="financeiro_titulos",
                registro_id=id_titulo,
                detalhes=f"{UsuarioSessao.nome} deu baixa no título #{id_titulo} ({tipo})."
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao gerar log de baixa do título financeiro: {log_err}")

        return True

    except Exception as e:
        print(f"❌ Erro ao dar baixa no título financeiro no Supabase: {e}")
        return False


def cancelar_titulo_financeiro(id_titulo, tipo):
    """Cancela um título pendente. Não apaga a linha — mantém o histórico para auditoria."""
    try:
        response = supabase_client.table("financeiro_titulos").update({"status": "CANCELADO"}).eq("id", int(id_titulo)).execute()

        if not response.data:
            return False

        try:
            registrar_log(
                acao=f"CANCELAMENTO_{tipo}",
                tabela="financeiro_titulos",
                registro_id=id_titulo,
                detalhes=f"{UsuarioSessao.nome} cancelou o título #{id_titulo} ({tipo})."
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao gerar log de cancelamento do título financeiro: {log_err}")

        return True

    except Exception as e:
        print(f"❌ Erro ao cancelar título financeiro no Supabase: {e}")
        return False
