import json
import random


class PensamentosSapo:

    def __init__(self):

        self.texto = None
        self.tempo_restante = 0
        self.ultimo_texto = None

        with open(
            "data/pensamentos_sapo.json",
            "r",
            encoding="utf-8"
        ) as arquivo:

            self.frases = json.load(
                arquivo
            )

        self.proxima_tentativa = random.uniform(
            120,
            300
        )

    def executar(
        self,
        categoria
    ):
        if self.texto:
            return

        frases = self.frases.get(
            categoria,
            []
        )

        if not frases:
            return

        disponiveis = [
            frase
            for frase in frases
            if frase != self.ultimo_texto
        ]

        if not disponiveis:
            disponiveis = frases

        self.texto = random.choice(
            disponiveis
        )

        self.ultimo_texto = (
            self.texto
        )

        self.tempo_restante = 6

    def atualizar(self, dt):
        if self.tempo_restante > 0:
            self.tempo_restante -= dt
            if self.tempo_restante <= 0:
                self.texto = None