def registrar_log(cursor, acao, tabela, registro_id=None, detalhes=None):
    """
    Função genérica para gravar logs. 
    O cursor deve ser passado para manter a mesma transação da query principal.
    """
    from utils.auth import UsuarioSessao

    # Se por algum motivo não houver sessão (ex: erro no login), evita que o log quebre o sistema
    u_id = UsuarioSessao.id if UsuarioSessao.id else 0
    u_nome = UsuarioSessao.nome if UsuarioSessao.nome else "Sistema/Desconhecido"
    u_nivel = UsuarioSessao.nivel if UsuarioSessao.nivel else 0

    sql = """
        INSERT INTO logs_sistema (
            usuario_id, usuario_login, nivel_acesso, 
            acao, tabela_afetada, registro_id, detalhes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    valores = (
        u_id,
        u_nome,
        u_nivel,
        acao,
        tabela,
        registro_id,
        detalhes
    )
    
    # Executa, mas NÃO dá commit aqui! 
    # O commit será dado na função que chamou o registrar_log.
    cursor.execute(sql, valores)