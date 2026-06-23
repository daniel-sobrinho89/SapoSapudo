from .personalidade_sapudo import PERSONALIDADE_SAPUDO


class ConversaSapudo:
    def __init__(self, client):
        self.client = client
        self.processando = False

    @property
    def model_manager(self):
        return self.client.model_manager

    @property
    def modelo_pronto(self):
        return self.client.inicializado

    def conversar(self, mensagem_usuario, contexto_extra=""):
        if self.processando:
            return {
                "texto": "Estou pensando na pergunta anterior.",
                "arquivo_audio": None,
            }

        self.processando = True

        if contexto_extra:
            prompt = f"""
Contexto atual:
{contexto_extra}

Usuário:
{mensagem_usuario}
"""
        else:
            prompt = mensagem_usuario

        try:
            resposta = self.client.gerar(prompt, PERSONALIDADE_SAPUDO)

            return resposta

        finally:
            self.processando = False
