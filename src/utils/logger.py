# utils/logs_service.py
from utils.auth import supabase_client as supabase  # Certifique-se de que o caminho do seu cliente está correto

def registrar_log(acao, tabela, registro_id=None, detalhes=None):
    """
    Função genérica para gravar logs diretamente no Supabase.
    Não necessita mais de cursor, pois a inserção é feita via API.
    """
    from utils.auth import UsuarioSessao

    # Evita que o sistema quebre caso não haja uma sessão ativa (ex: falha antes do login)
    u_id = UsuarioSessao.id if UsuarioSessao.id else None  # Mudado para None se o ID for chave estrangeira nula no banco
    u_nome = UsuarioSessao.nome if UsuarioSessao.nome else "Sistema/Desconhecido"
    u_nivel = UsuarioSessao.nivel if UsuarioSessao.nivel else 0

    try:
        # Monta os dados para inserção no formato que o Supabase/PostgREST espera (Dicionário)
        dados_log = {
            "usuario_id": u_id,
            "usuario_login": u_nome,
            "nivel_acesso": u_nivel,
            "acao": acao,
            "tabela_afetada": tabela,
            "registro_id": registro_id,
            "detalhes": detalhes
        }

        # Executa o insert direto na tabela do Supabase
        resposta = supabase.table("logs_sistema").insert(dados_log).execute()
        
        # Opcional: Retorna True se a gravação deu certo
        return True
    except Exception as e:
        print(f"Erro ao registrar log no Supabase: {e}")
        return False