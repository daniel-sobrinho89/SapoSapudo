import json
import random


class LivroClimatico:
    def __init__(self):
        with open("data/livro_climatico.json", encoding="utf-8") as arquivo:
            self.frases = json.load(arquivo)

    def gerar_texto_narracao(self, clima):
        temperatura = getattr(clima, "temperature", 0)
        umidade = getattr(clima, "humidity", 0)
        velocidade_vento = getattr(clima, "wind_speed", 0)
        direcao_vento = self.obter_direcao_vento(getattr(clima, "wind_direction", 0))
        nuvens = getattr(clima, "cloudiness", 0)
        previsao_nuvens = getattr(clima, "future_cloudiness_3h", nuvens)

        frases = []

        if temperatura <= 15:
            frases.append(
                f"Hum... hoje o lago acordou com {temperatura:.0f} graus. "
                "Uma temperatura excelente para uma boa leitura."
            )
        elif temperatura >= 28:
            frases.append(
                f"Hoje o calor chegou com {temperatura:.0f} graus, como se o "
                "próprio sol quisesse virar página."
            )
        else:
            frases.append(
                f"Hum... hoje o lago acordou com {temperatura:.0f} graus. "
                "Uma temperatura excelente para uma boa leitura."
            )

        if umidade >= 80:
            frases.append(
                "A umidade está bem alta. Até as páginas deste livro "
                "parecem um pouco úmidas."
            )

        if velocidade_vento >= 20:
            frases.append(
                f"O vento resolveu passear pelo {direcao_vento} e está "
                "soprando com certa vontade."
            )

        if nuvens >= 70 or previsao_nuvens >= 70:
            frases.append(
                "Segundo este velho livro climático, existe chance de chuva "
                "nas próximas horas. Talvez seja uma boa ideia encontrar uma "
                "folha grande antes que ela comece."
            )
        elif nuvens >= 40:
            frases.append(
                "As nuvens estão se organizando como um bando de capivaras curiosas."
            )

        if not frases:
            return (
                "O velho livro climático abriu uma página tranquila e resolveu "
                "contar um segredo de céu limpo."
            )

        return random.choice(frases)

    def gerar_pagina(self, clima):
        direcao_vento = self.obter_direcao_vento(clima.wind_direction)

        # ==========================
        # ESCOLHE CATEGORIA
        # ==========================

        categorias = []
        if clima.cloudiness >= 70:
            categorias.append("chuva")
        if clima.temperature <= 15:
            categorias.append("frio")
        if clima.humidity >= 80:
            categorias.append("umidade")
        if clima.wind_speed >= 20:
            categorias.append("vento")
        if not categorias:
            categorias.append("sol")

        categoria = random.choice(categorias)

        # ==========================
        # TEXTO ESQUERDA
        # ==========================

        texto = random.choice(self.frases[categoria])

        linhas_processadas = []
        for linha in texto["linhas"]:
            linhas_processadas.append(linha.replace("{direcao}", direcao_vento))

        # ==========================
        # RETORNO
        # ==========================
        pagina_direita = self.gerar_previsao_nuvens(clima)

        return {
            "pagina_esquerda": {
                "titulo": texto["titulo"],
                "linhas": linhas_processadas,
            },
            "pagina_direita": pagina_direita,
        }

    def obter_direcao_vento(self, graus):
        direcoes = [
            "norte",
            "nordeste",
            "leste",
            "sudeste",
            "sul",
            "sudoeste",
            "oeste",
            "noroeste",
        ]

        indice = round(graus / 45) % 8

        return direcoes[indice]

    def gerar_previsao_nuvens(self, clima):
        agora = clima.cloudiness
        h1 = clima.future_cloudiness_1h
        h2 = clima.future_cloudiness_2h
        h3 = clima.future_cloudiness_3h

        tendencia = h3 - agora

        if tendencia >= 30:
            titulo = "As Nuvens Crescem"

            linhas = [
                "A presença das nuvens aumentará nas próximas horas.",
                "",
                f"Céu coberto agora: {agora:.0f}%",
                f"Em 1 hora: {h1:.0f}%",
                f"Em 2 horas: {h2:.0f}%",
                "",
                "Talvez a chuva esteja apenas esperando o momento certo para chegar.",
            ]

        elif tendencia <= -30:
            titulo = "O Céu se Abrirá"

            linhas = [
                "As nuvens perderão espaço ao longo das próximas horas.",
                "",
                f"Céu coberto agora: {agora:.0f}%",
                f"Em 1 hora: {h1:.0f}%",
                f"Em 2 horas: {h2:.0f}%",
                "",
                "A luz encontrará espaço para atravessar o céu novamente.",
            ]

        else:
            titulo = "Poucas Mudanças"

            linhas = [
                "A quantidade de nuvens mudará muito pouco.",
                "",
                f"Céu coberto agora: {agora:.0f}%",
                f"Em 1 hora: {h1:.0f}%",
                f"Em 2 horas: {h2:.0f}%",
                "",
                "Nem toda previsão fala de mudanças.",
                "Às vezes ela fala de paz.",
            ]

        return {"titulo": titulo, "linhas": linhas}
