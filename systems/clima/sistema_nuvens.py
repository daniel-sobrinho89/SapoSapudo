# ==========================================
# sistema_nuvens.py
# ==========================================

import pygame_adapter

from systems.clima.nuvem import Nuvem


class SistemaNuvens:

    def __init__(
        self, 
        transform
    ):

        self.atualizar_area_interna()

        self.intensidade = 0
        self.wind_direction = 0
        self.wind_speed = 0
        self.transform = transform
        Nuvem.iniciar_carregamento()

        # nuvens ativas
        self.nuvens = []

        # pool pré-criado
        self.pool_nuvens = []

    # ==========================================
    # ATUALIZAR ÁREA
    # ==========================================
    def atualizar_area_interna(self):
        from config import LARGURA

        self.area_interna = pygame_adapter.Rect(
            0,
            0,
            LARGURA,
            320
        )

    # ==========================================
    # CALCULAR INTENSIDADE
    # ==========================================

    def calcular_intensidade(
        self,
        atual,
        futuro_1h,
        futuro_2h,
        futuro_3h
    ):

        intensidade = atual

        # crescimento gradual futuro

        if futuro_3h > atual:

            intensidade += (
                (futuro_1h - atual) * 0.2
            )

            intensidade += (
                (futuro_2h - atual) * 0.3
            )

            intensidade += (
                (futuro_3h - atual) * 0.5
            )

        intensidade = max(
            0,
            min(100, intensidade)
        )

        return intensidade

    # ==========================================
    # UPDATE
    # ==========================================

    def atualizar(
        self,
        dt,
        cloudiness,
        future_1h,
        future_2h,
        future_3h,
        wind_direction,
        wind_speed
    ):
        if not Nuvem.carregado:
            return

        self.intensidade = self.calcular_intensidade(
            cloudiness,
            future_1h,
            future_2h,
            future_3h
        )

        # quantidade de nuvens
        if self.intensidade <= 5:
            alvo = 2
        else:
            alvo = max(1, round(self.intensidade / 16))

        # escala geral
        escala = max(
            0.7,
            self.intensidade / 100
        )

        self.wind_direction = wind_direction
        self.wind_speed = wind_speed

        # propagar direção/velocidade do vento para nuvens existentes
        for nuvem in self.nuvens:
            nuvem.wind_direction = self.wind_direction
            nuvem.wind_speed = self.wind_speed

        # cria nuvens
        while len(self.nuvens) < alvo:
            ceu_limpo = self.intensidade <= 5

            nova_nuvem = Nuvem(
                self.area_interna,
                self.transform,
                intensidade=escala,
                wind_direction=self.wind_direction,
                wind_speed=self.wind_speed,
                ceu_limpo=ceu_limpo
            )

            pode_adicionar = True

            for nuvem in self.nuvens:

                distancia_x = abs(
                    nova_nuvem.x - nuvem.x
                )

                distancia_y = abs(
                    nova_nuvem.y - nuvem.y
                )

                if (
                    distancia_x < 380
                    and distancia_y < 120
                ):
                    pode_adicionar = False
                    break

            if pode_adicionar:

                self.nuvens.append(
                    nova_nuvem
                )

            else:

                break

        # remove nuvens extras se houver mais do que o alvo
        while len(self.nuvens) > alvo:

            self.nuvens.pop()

        # atualiza nuvens e mantém apenas as vivas
        nuvens_ativas = []

        for nuvem in self.nuvens:
            if nuvem.atualizar(dt):
                nuvens_ativas.append(nuvem)

        self.nuvens = nuvens_ativas

    # ==========================================
    # RENDER
    # ==========================================
    def limpar(self):
        self.nuvens.clear()

    def renderizar(
        self,
        tela,
        eh_dia=False
    ):
        if not Nuvem.carregado:
            return
        
        for nuvem in self.nuvens:
            nuvem.renderizar(
                tela,
                eh_dia
            )