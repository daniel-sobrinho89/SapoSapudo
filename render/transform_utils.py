import pygame


class TransformUtils:

    def __init__(self):

        self.cache_escalas = {}

    def escalar(self, imagem, escala):

        key = (
            id(imagem),
            round(escala, 4)
        )

        if key in self.cache_escalas:

            return self.cache_escalas[key]

        largura = max(
            1,
            int(imagem.get_width() * escala)
        )

        altura = max(
            1,
            int(imagem.get_height() * escala)
        )

        escalada = pygame.transform.smoothscale(
            imagem,
            (largura, altura)
        )

        self.cache_escalas[key] = escalada

        return escalada

    def rotacionar(self, imagem, rotacao):

        return pygame.transform.rotate(
            imagem,
            rotacao
        )