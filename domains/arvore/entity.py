from core.animacoes import Animacoes


class Arvore:
    TEMPO_CRESCIMENTO = 180.0
    ESCALA_INICIAL = 0.18
    ESCALA_FINAL = 1.0

    def __init__(self, nome, x, y, altura):
        self.nome = nome
        self.x = x
        self.y = y
        self.altura = altura
        self.animacoes = Animacoes(nome)
        self.madeira = 8
        self.vida = 8
        self.corpo_rect = None
        self.escala_x = self.ESCALA_FINAL
        self.escala_y = self.ESCALA_FINAL
        self.crescendo = False
        self.tempo_crescimento = self.TEMPO_CRESCIMENTO

    @property
    def pronta_para_coleta(self):
        return not self.crescendo and self.madeira > 0

    def iniciar_crescimento(self):
        self.crescendo = True
        self.tempo_crescimento = 0.0
        self.escala_x = self.ESCALA_INICIAL
        self.escala_y = self.ESCALA_INICIAL
        self.madeira = 0
        self.vida = 0
        self.animacoes.definir("ocioso")

    def atualizar(self, dt):
        self.animacoes.atualizar(dt)
        if not self.crescendo:
            return

        self.tempo_crescimento = min(
            self.TEMPO_CRESCIMENTO, self.tempo_crescimento + max(0.0, dt)
        )
        progresso = self.tempo_crescimento / self.TEMPO_CRESCIMENTO
        # Crescimento linear e lento para ficar visualmente perceptível.
        escala = (
            self.ESCALA_INICIAL + (self.ESCALA_FINAL - self.ESCALA_INICIAL) * progresso
        )
        self.escala_x = escala
        self.escala_y = escala
        if self.tempo_crescimento >= self.TEMPO_CRESCIMENTO:
            self.crescendo = False
            self.madeira = 8
            self.vida = 8
            self.escala_x = self.ESCALA_FINAL
            self.escala_y = self.ESCALA_FINAL
            self.animacoes.definir("ocioso")

    def restaurar_estado_save(self, dados):
        """Reconstrói o estado visual derivado a partir do snapshot salvo."""
        if getattr(self, "crescendo", False):
            self.animacoes.definir("ocioso")
            return
        if getattr(self, "madeira", 0) <= 0:
            self.animacoes.definir("cortada")
        else:
            self.animacoes.definir("ocioso")

    def obter_madeira(self):
        if not self.pronta_para_coleta:
            return False
        if self.madeira <= 0:
            self.madeira = 0
            self.animacoes.definir("cortada")
            return False

        self.madeira -= 1
        if self.madeira == 0:
            self.animacoes.definir("cortada")

        return True
