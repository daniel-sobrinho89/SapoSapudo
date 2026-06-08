import random
import math

from config import *

from systems.animacoes_semente import (
    aplicar_vento as sistema_aplicar_vento,
    atualizar_piscada as sistema_atualizar_piscada,
)

from systems.fisica import (
    sistema_fisica,
)


class Semente:

    def __init__(self):
        self.x = 500
        self.y = 520
        self.vel_x = 0
        self.vel_y = 0
        self.gravidade = 220
        self.largura = 30
        self.altura = 30
        self.no_chao = True
        self.sorrindo = False
        self.piscando = False

        self.timer_piscada = random.uniform(
            2,
            5
        )

        self.duracao_piscada = 0.15
        self.tempo_piscando = 0

        self.timer_movimento = random.uniform(
            4,
            8
        )

        self.altura_salto = -120
        self.limite_chao = 560
        self.limite_esquerda = 20
        self.limite_direita = 1024
        self.flutuando = False
        self.estado = "parado"

        # rajada moved to ClimaService

        self.tempo_flutuando = 0

        self.direcao_pulo = random.choice(
            [-1, 1]
        )

        self.fase_flutuacao = random.uniform(
            0,
            math.pi * 2
        )

        self.offset_flutuacao_x = 0
        self.offset_flutuacao_y = 0
        self.altura_alvo_flutuacao = 0
        self.timer_altura_vento = 0
        self.pulos_restantes = 0
        self.sustentacao_restante = 0
        self.estava_flutuando = False
        self.pousando_do_vento = False

    def iniciar_pulo_lateral(self):
        if self.x <= self.limite_esquerda + 20:
            self.direcao_pulo = 1

        elif self.x >= self.limite_direita - 20:
            self.direcao_pulo = -1

        else:
            if random.random() < 0.10:
                self.direcao_pulo *= -1

        self.vel_x = (
            self.direcao_pulo * 60
        )

        self.vel_y = (
            self.altura_salto
        )

    def definir_estado(self, novo_estado):
        self.estado = novo_estado

    def entrar_flutuando(self):
        self.flutuando = True
        self.sorrindo = False
        self.estava_flutuando = True
        self.definir_estado("flutuando")

    def sair_flutuando(self):
        self.flutuando = False
        self.estava_flutuando = False
        # estado posterior será avaliado por resolver_limites/ao_pousar

    def marcar_pousando_do_vento(self):
        self.pousando_do_vento = True
        self.estava_flutuando = False

    def atualizar_temporizadores(self, dt):
        # timer_movimento apenas decresce quando está no chão e não vem do vento
        if (
            self.no_chao
            and not self.flutuando
            and not self.pousando_do_vento
        ):
            self.timer_movimento -= dt

        # rajada agora é gerida por ClimaService (veja clima_service.rajada_ativa)

        # timer de mudança de altura do vento (controle de alvo de flutuação)
        self.timer_altura_vento -= dt

        if self.timer_altura_vento <= 0:
            self.altura_alvo_flutuacao = (
                random.uniform(
                    180,
                    350
                )
            )

            self.timer_altura_vento = (
                random.uniform(
                    0.8,
                    2
                )
            )

    def ao_pousar(self, pousou_agora):
        # Ações ao pousar: se veio do vento, dar um tempo antes de mover
        if (
            pousou_agora
            and self.pousando_do_vento
        ):
            self.timer_movimento = (
                random.uniform(
                    3,
                    6
                )
            )

            self.pulos_restantes = 0

        # Garantir limpeza do flag de pousando_do_vento
        if self.pousando_do_vento:
            self.pousando_do_vento = False

    def gerar_quantidade_pulos(self):
        sorteio = random.random()

        if sorteio < 0.60:
            return 2

        if sorteio < 0.85:
            return 3

        if sorteio < 0.95:
            return 4

        return 5

    def aplicar_vento(
        self,
        clima_service,
        dt
    ):
        return sistema_aplicar_vento(self, clima_service, dt)

    def atualizar_piscada(
        self,
        dt
    ):
        return sistema_atualizar_piscada(self, dt)

    def atualizar(
        self,
        dt,
        clima_service
    ):
        self.atualizar_piscada(dt)

        # Atualiza temporizadores (movimento, rajada e altura do vento)
        self.atualizar_temporizadores(dt)

        if (
            self.no_chao
            and not self.flutuando
            and not self.pousando_do_vento
            and self.timer_movimento <= 0
        ):

            if self.pulos_restantes <= 0:

                self.pulos_restantes = (
                    self.gerar_quantidade_pulos()
                )

            self.iniciar_pulo_lateral()
            self.pulos_restantes -= 1

            if self.pulos_restantes > 0:
                self.timer_movimento = (
                    random.uniform(
                        0.6,
                        1.2
                    )
                )

            else:
                self.timer_movimento = (
                    random.uniform(
                        4,
                        8
                    )
                )

        self.aplicar_vento(
            clima_service,
            dt
        )

        # Física: gravidade, integração de movimento e resolução de limites
        sistema_fisica.aplicar_gravidade(self, dt)
        sistema_fisica.integrar_movimento(self, dt)
        sistema_fisica.resolver_limites(self, clima_service)

        if self.x <= self.limite_esquerda:
            self.x = self.limite_esquerda

            if self.vel_x < 0:
                self.vel_x = 0
                self.direcao_pulo = 1

        elif self.x >= self.limite_direita:
            self.x = self.limite_direita

            if self.vel_x > 0:
                self.vel_x = 0
                self.direcao_pulo = -1