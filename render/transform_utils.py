import pygame_adapter


class TransformUtils:

    def __init__(self):

        self.cache_escalas = {}
        self.cache_rotacoes = {}

    def escalar(self, imagem, tamanho):

        largura, altura = tamanho

        key = (
            id(imagem),
            largura,
            altura
        )

        if key in self.cache_escalas:
            return self.cache_escalas[key]

        escalada = pygame_adapter.transform.smoothscale(
            imagem,
            (largura, altura)
        )

        self.cache_escalas[key] = escalada

        return escalada

    def rotacionar(
        self,
        imagem,
        rotacao
    ):

        rotacao = round(rotacao)

        key = (
            id(imagem),
            rotacao
        )

        if key in self.cache_rotacoes:
            return self.cache_rotacoes[key]

        resultado = pygame_adapter.transform.rotate(
            imagem,
            rotacao
        )

        self.cache_rotacoes[key] = resultado

        return resultado