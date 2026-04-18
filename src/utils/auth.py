from utils.db_config import DB_CONFIG
import psycopg2
import bcrypt

class UsuarioSessao:
    """O 'Crachá' digital que fica na memória do sistema enquanto ele estiver aberto."""
    id = None
    nome = None
    usuario = None
    nivel = None

    @classmethod
    def definir_usuario(cls, dados):
        """Preenche os dados da sessão (id, nome, usuario, nivel)."""
        cls.id = dados[0]
        cls.nome = dados[1]
        cls.usuario = dados[2]
        cls.nivel = dados[3]

    @classmethod
    def limpar_sessao(cls):
        """Limpa os dados ao fazer logout."""
        cls.id = cls.nome = cls.usuario = cls.nivel = None

def verificar_login(usuario_digitado, senha_digitada):
    """Consulta o banco, valida a senha e preenche a sessão do usuário."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Agora buscamos tudo: id, nome, usuario, nivel e a senha (pass)
        # Ajustei a ordem conforme a lógica da nossa classe
        query = "SELECT id, nome, usuario, nivel, pass FROM login WHERE usuario = %s"
        cur.execute(query, (usuario_digitado,))
        resultado = cur.fetchone()

        cur.close()

        if resultado:
            # resultado[4] é onde está a senha (pass) no nosso SELECT acima
            hash_no_banco = resultado[4]
            
            if bcrypt.checkpw(senha_digitada.encode('utf-8'), hash_no_banco.encode('utf-8')):
                # SE A SENHA BATE: Preenchemos o crachá antes de retornar True
                # Passamos apenas (id, nome, usuario, nivel) para a classe
                dados_sessao = (resultado[0], resultado[1], resultado[2], resultado[3])
                UsuarioSessao.definir_usuario(dados_sessao)
                
                print(f"Sessão iniciada para: {UsuarioSessao.nome} (Nível: {UsuarioSessao.nivel})")
                return True
        
        return False

    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return False
    finally:
        if conn:
            conn.close()