import json
import random


class LivroClimatico:

    def __init__(self):

        with open(
            "data/livro_climatico.json",
            "r",
            encoding="utf-8"
        ) as arquivo:

            self.frases = json.load(
                arquivo
            )

    def gerar_pagina(
        self,
        clima
    ):
        direcao_vento = self.obter_direcao_vento(
            clima.wind_direction
        )

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

        texto = random.choice(
            self.frases[categoria]
        )

        linhas_processadas = []
        for linha in texto["linhas"]:
            linhas_processadas.append(
                linha.replace(
                    "{direcao}",
                    direcao_vento
                )
            )

        # ==========================
        # RETORNO
        # ==========================
        pagina_direita = self.gerar_previsao_nuvens(clima)

        return {

            "pagina_esquerda": {
                "titulo": texto["titulo"],
                "linhas": linhas_processadas
            },

            "pagina_direita": pagina_direita
        }
    
    def obter_direcao_vento(
        self,
        graus
    ):
        direcoes = [
            "norte",
            "nordeste",
            "leste",
            "sudeste",
            "sul",
            "sudoeste",
            "oeste",
            "noroeste"
        ]

        indice = round(
            graus / 45
        ) % 8

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
                "Talvez a chuva esteja apenas esperando o momento certo para chegar."
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
                "A luz encontrará espaço para atravessar o céu novamente."
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
                "Às vezes ela fala de paz."
            ]

        return {
            "titulo": titulo,
            "linhas": linhas
        }