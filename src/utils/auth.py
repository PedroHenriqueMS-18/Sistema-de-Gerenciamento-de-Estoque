import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import bcrypt

# 💡 SOLUÇÃO DIRETRIZ: Descobre a pasta raiz do projeto e força a leitura do .env correto
raiz_do_projeto = Path(__file__).resolve().parent.parent
caminho_env = raiz_do_projeto / '.env'

# Carrega o .env apontando diretamente para o arquivo físico
load_dotenv(dotenv_path=caminho_env)

# Captura e limpa as strings contra espaços invisíveis
url_env = os.getenv("SUPABASE_URL")
key_env = os.getenv("SUPABASE_ANON_KEY")

URL_LIMPA = url_env.strip() if url_env else ""
KEY_LIMPA = key_env.strip() if key_env else ""

# Inicializa o cliente oficial do Supabase com superpoderes
supabase_client = create_client(URL_LIMPA, KEY_LIMPA)

class UsuarioSessao:
    """O 'Crachá' digital que fica na memória do sistema enquanto ele estiver aberto."""
    id = None
    nome = None
    usuario = None
    nivel = None

    @classmethod
    def definir_usuario(cls, dados):
        """Preenche os dados da sessão (id, nome, usuario, nivel)."""
        cls.id = dados.get("id")
        cls.nome = dados.get("nome")
        cls.usuario = dados.get("usuario")
        cls.nivel = dados.get("nivel")

    @classmethod
    def limpar_sessao(cls):
        """Limpa os dados ao fazer logout."""
        cls.id = cls.nome = cls.usuario = cls.nivel = None


def verificar_login(usuario_digitado, senha_digitada):
    """Consulta o Supabase via API Oficial usando superpoderes da service_role."""
    try:
        print(f"🔄 Tentando autenticar usuário '{usuario_digitado}' via API Oficial...")
        
        # Faz a busca usando o cliente oficial protegido
        response = supabase_client.table("login").select("id, nome, usuario, nivel, pass").eq("usuario", usuario_digitado).execute()
        
        if response.data:
            usuario_encontrado = response.data[0]
            hash_no_banco = usuario_encontrado.get("pass")
            
            # Validação segura da senha criptografada (Bcrypt)
            if bcrypt.checkpw(senha_digitada.encode('utf-8'), hash_no_banco.encode('utf-8')):
                UsuarioSessao.definir_usuario(usuario_encontrado)
                print(f"🚀 SUCESSO ABSOLUTO! Tela liberada para: {UsuarioSessao.nome}")
                return True
        
        print("❌ Usuário ou senha incorretos na resposta do banco.")
        return False

    except Exception as e:
        print(f"❌ Erro crítico na autenticação: {e}")
        return False


def verificar_senha_supervisor(usuario_digitado, senha_digitada):
    """
    Confere se um usuário/senha pertence a um supervisor (nível 1), SEM alterar
    a sessão do operador atualmente logado (UsuarioSessao). Usado como trava de
    segurança em operações sensíveis do PDV, como a Sangria de caixa.
    """
    try:
        response = supabase_client.table("login")\
            .select("nivel, pass, ativo")\
            .eq("usuario", usuario_digitado)\
            .execute()

        if not response.data:
            return False

        usuario_encontrado = response.data[0]

        # Só autoriza se o usuário informado for realmente um supervisor (nível 1) e estiver ativo
        if usuario_encontrado.get("nivel") != 1 or usuario_encontrado.get("ativo") is False:
            return False

        hash_no_banco = usuario_encontrado.get("pass")
        return bcrypt.checkpw(senha_digitada.encode('utf-8'), hash_no_banco.encode('utf-8'))

    except Exception as e:
        print(f"❌ Erro ao verificar autorização de supervisor: {e}")
        return False