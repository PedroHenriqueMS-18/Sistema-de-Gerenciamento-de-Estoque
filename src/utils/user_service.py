from utils.auth import supabase_client, UsuarioSessao
from utils.logger import registrar_log
from tkinter import messagebox
import bcrypt

def buscar_usuarios_db(termo_busca="", mostrar_inativos=0, filtro="Nome"):
    """Busca usuários no Supabase baseada no termo, status e campo selecionado."""
    try:
        query = supabase_client.table("login").select("id, nome, usuario, nivel, ativo")
        
        if not mostrar_inativos:
            query = query.eq("ativo", True)

        if termo_busca:
            mapeamento = {
                "ID": "id",
                "Nome": "nome",
                "Usuário": "usuario"
            }
            coluna_selecionada = mapeamento.get(filtro, "nome")

            if filtro == "ID":
                if termo_busca.isdigit():
                    query = query.eq(coluna_selecionada, int(termo_busca))
                else:
                    query = query.eq("id", -1) 
            else:
                query = query.ilike(coluna_selecionada, f"%{termo_busca}%")
        
        query = query.order("nome", desc=False)
        response = query.execute()

        dados_tupla = []
        if response.data:
            for item in response.data:
                dados_tupla.append((
                    item.get("id"),
                    item.get("nome"),
                    item.get("usuario"),
                    item.get("nivel"),
                    item.get("ativo")
                ))
        return dados_tupla
    except Exception as e:
        print(f"❌ Erro ao buscar usuários no Supabase: {e}")
        return []

def buscar_usuario_por_id(user_id):
    """Busca os detalhes de um único usuário pelo ID."""
    try:
        response = supabase_client.table("login").select("id, nome, usuario, nivel, ativo, cpf").eq("id", user_id).execute()
        if response.data:
            item = response.data[0]
            return {
                "id": item.get("id"),
                "nome": item.get("nome"),
                "login": item.get("usuario"), # Mapeado para 'login' conforme seu modal espera
                "nivel": item.get("nivel"),
                "ativo": item.get("ativo"),
                "cpf": item.get("cpf")
            }
        return None
    except Exception as e:
        print(f"❌ Erro ao buscar detalhes do usuário: {e}")
        return None

def atualizar_usuario_db(dados):
    """Atualiza os dados cadastrais do funcionário e gera log comparativo."""
    try:
        antigo = buscar_usuario_por_id(dados['id'])
        if not antigo:
            return False

        nivel_novo = int(dados['nivel'])
        id_usuario_alvo = int(dados['id'])

        valores_update = {
            "nome": dados['nome'],
            "usuario": dados['login'],
            "cpf": dados['cpf'],
            "nivel": nivel_novo
        }
        supabase_client.table("login").update(valores_update).eq("id", id_usuario_alvo).execute()

        mudancas = []
        if antigo['nome'] != dados['nome']:
            mudancas.append(f"Nome: '{antigo['nome']}' -> '{dados['nome']}'")
        if antigo['login'] != dados['login']:
            mudancas.append(f"Login: '{antigo['login']}' -> '{dados['login']}'")
        if antigo['cpf'] != dados['cpf']:
            mudancas.append(f"CPF: '{antigo['cpf']}' -> '{dados['cpf']}'")
        if int(antigo['nivel']) != nivel_novo:
            mudancas.append(f"Nível: {antigo['nivel']} -> {nivel_novo}")

        detalhes_finais = " | ".join(mudancas) if mudancas else "Dados salvos sem alterações."

        try:
            registrar_log(
                cursor=None,
                acao="ALTERAÇÃO DE PERFIL",
                tabela="login",
                registro_id=id_usuario_alvo,
                detalhes=f"Alterado por {UsuarioSessao.nome} | " + detalhes_finais
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao registrar log de perfil: {log_err}")

        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar usuário no Supabase: {e}")
        return False

def inativar_usuario_db(usuario_id):
    """Desativa o acesso de um funcionário no sistema."""
    try:
        supabase_client.table("login").update({"ativo": False}).eq("id", usuario_id).execute()
        
        try:
            registrar_log(
                cursor=None,
                acao="INATIVAÇÃO",
                tabela="login", # 🐛 Corrigido: era 'produtos' no seu código original
                registro_id=usuario_id,
                detalhes=f"O funcionário (ID: {usuario_id}) foi inativado por {UsuarioSessao.nome}."
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao registrar log de inativação: {log_err}")
        return True
    except Exception as e:
        print(f"❌ Erro ao inativar usuário no Supabase: {e}")
        return False

def reativar_usuario_db(usuario_id):
    """Reativa o acesso de um funcionário no sistema."""
    try:
        supabase_client.table("login").update({"ativo": True}).eq("id", usuario_id).execute()
        
        try:
            registrar_log(
                cursor=None,
                acao="REATIVAÇÃO",
                tabela="login", # 🐛 Corrigido: era 'produtos' no seu código original
                registro_id=usuario_id,
                detalhes=f"O funcionário (ID: {usuario_id}) foi reativado por {UsuarioSessao.nome}."
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao registrar log de reativação: {log_err}")
        return True
    except Exception as e:
        print(f"❌ Erro ao reativar usuário no Supabase: {e}")
        return False

def cadastrar_usuario_db(dados):
    """Cadastra um novo colaborador criptografando a senha com bcrypt."""
    try:
        senha_plana = dados['senha'].encode('utf-8')
        hash_gerado = bcrypt.hashpw(senha_plana, bcrypt.gensalt())

        valores_insert = {
            "nome": dados['nome'],
            "cpf": dados['cpf'],
            "usuario": dados['login'],
            "nivel": int(dados['nivel']),
            "pass": hash_gerado.decode('utf-8'),
            "ativo": True
        }
        
        response = supabase_client.table("login").insert(valores_insert).execute()
        
        novo_usuario_id = None
        if response.data:
            novo_usuario_id = response.data[0].get("id")

        niveis_map = {1: "Administrador", 2: "Operador", 3: "Vendedor"}
        nivel_nome = niveis_map.get(int(dados['nivel']), "Desconhecido")
        
        detalhe_log = (f"O administrador {UsuarioSessao.nome} cadastrou um novo funcionário: "
                       f"{dados['nome']} | Login: {dados['login']} | Nível: {nivel_nome}")

        try:
            registrar_log(
                cursor=None,
                acao="CADASTRO USUÁRIO",
                tabela="login",
                registro_id=novo_usuario_id,
                detalhes=detalhe_log
            )
        except Exception as log_err:
            print(f"⚠️ Erro ao registrar log de novo usuário: {log_err}")

        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao cadastrar usuário no Supabase: {e}")
        return False