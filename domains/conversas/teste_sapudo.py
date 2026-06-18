from domains.conversas.conversa_sapudo import ConversaSapudo
from domains.conversas.gemini_client import GeminiClient

API_KEY = "AQ.Ab8RN6KJ70zkPn3FVG3EWR4HtZomCLzShmwnzNyRc22OhjUjfA"


def main():
    gemini = GeminiClient(api_key=API_KEY)

    conversa = ConversaSapudo(gemini=gemini)

    contexto_extra = """
Estado: acordado
Clima: ensolarado
Hora: manhã
Musica: nenhuma
"""

    mensagem = "Olá Sapudo, o que tem de bom em São Paulo hoje?"

    resposta = conversa.conversar(
        mensagem_usuario=mensagem, contexto_extra=contexto_extra
    )

    print()
    print("Usuário:")
    print(mensagem)

    print()
    print("Sapudo:")
    print(resposta)
    print()


if __name__ == "__main__":
    main()
