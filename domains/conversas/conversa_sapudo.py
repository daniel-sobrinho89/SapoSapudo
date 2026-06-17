from .personalidade_sapudo import PERSONALIDADE_SAPUDO


class ConversaSapudo:
    def __init__(self, gemini):
        self.gemini = gemini

        self.processando = False

    def conversar(self, mensagem_usuario, contexto_extra=""):
        if self.processando:
            return "Estou pensando na pergunta anterior."

        self.processando = True

        prompt = f"""
    {PERSONALIDADE_SAPUDO}

    Contexto atual:

    {contexto_extra}

    Usuário:
    {mensagem_usuario}

    Responda como Sapudo.
    """

        try:
            resposta = self.gemini.gerar(prompt)

            return resposta

        finally:
            self.processando = False
