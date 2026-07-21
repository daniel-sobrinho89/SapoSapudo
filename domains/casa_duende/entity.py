import math
import random

import kivy_adapter
from domains.casa_duende.animacoes import AnimacoesCasaDuende


class CasaDuende:
    def __init__(self, transform):
        self.transform = transform
        self.x = 550
        self.y = 155
        self.animacoes = AnimacoesCasaDuende()

        # =====================================
        # NEVOA
        # =====================================
        self.tempo_nevoa = 0.0
        self.nevoa_bolhas = []
        for _ in range(40):
            self.nevoa_bolhas.append(
                {
                    "x": random.random(),
                    "y": random.random(),
                    "raio": random.randint(15, 40),
                    "fase": random.uniform(0, 6.28),
                    "velocidade": random.uniform(0.3, 1.2),
                }
            )

    def atualizar(self, dt):
        self.tempo_nevoa += dt
        self.animacoes.atualizar(dt)
        # self.atualizar_posicao(centro_y)

    # =====================================
    # RENDER
    # =====================================
    def atualizar_layout_casa(
        self,
        largura,
        altura,
    ):
        self.largura = largura
        self.altura = altura

        self._reconstruir_areas()

    def atualizar_posicao(self):
        self.area_interna.x = self.x + self.area_interna_offset_x
        self.area_interna.y = self.y + self.area_interna_offset_y

        self.area_particulas.x = self.x + 40
        self.area_particulas.y = self.y + 40

        self.area_casa.x = (
            self.x + self.area_interna_offset_x + int(self.area_interna.width * 0.10)
        )

        self.area_casa.y = self.y + self.area_interna_offset_y - int(self.altura * 0.07)

    def _reconstruir_areas(self):
        self.area_interna_offset_x = int(self.largura * 0.10)
        self.area_interna_offset_y = int(self.altura * 0.24)
        self.area_interna_width = int(self.largura * 0.80)
        self.area_interna_height = int(self.altura * 0.62)

        self.area_interna = kivy_adapter.Rect(
            self.x + self.area_interna_offset_x,
            self.y + self.area_interna_offset_y,
            self.area_interna_width,
            self.area_interna_height,
        )

        self.area_particulas = kivy_adapter.Rect(
            self.x + 40,
            self.y - 180,
            self.largura - 130,
            self.altura - 180,
        )

        casa_x = self.x + int(self.largura * 0.18)
        casa_y = self.y + int(self.altura * 0.10)
        casa_w = int(self.largura * 0.67)
        casa_h = int(self.altura * 0.50)

        self.area_casa = kivy_adapter.Rect(
            casa_x,
            casa_y,
            casa_w,
            casa_h,
        )

    # =====================================
    # RENDER
    # =====================================

    def desenhar_nevoa(self, tela, intensidade):
        tempo = self.tempo_nevoa

        if intensidade <= 0:
            return

        quantidade = len(self.nevoa_bolhas)

        alpha_base = int((intensidade / 7.0) * 120)

        for bolha in self.nevoa_bolhas[:quantidade]:
            raio = bolha["raio"]

            x = int(
                self.area_casa.centerx
                + (bolha["x"] - 0.5) * self.area_casa.width * 0.8
                + math.cos(tempo * bolha["velocidade"] * 0.6 + bolha["fase"]) * 8
            )

            y = int(
                self.area_casa.centery
                + (bolha["y"] - 0.5) * self.area_casa.height * 0.8
                + math.sin(tempo * bolha["velocidade"] + bolha["fase"]) * 12
            )

            x = max(self.area_casa.left + raio, min(x, self.area_casa.right - raio))

            y = max(self.area_casa.top + raio, min(y, self.area_casa.bottom - raio))

            superficie = kivy_adapter.Surface(
                (raio * 2, raio * 2), kivy_adapter.SRCALPHA
            )

            kivy_adapter.draw.circle(
                superficie, (220, 235, 255, int(alpha_base * 0.15)), (raio, raio), raio
            )

            kivy_adapter.draw.circle(
                superficie,
                (220, 235, 255, int(alpha_base * 0.40)),
                (raio, raio),
                int(raio * 0.70),
            )

            kivy_adapter.draw.circle(
                superficie,
                (235, 245, 255, int(alpha_base * 0.80)),
                (raio, raio),
                int(raio * 0.35),
            )

            tela.blit(superficie, (x - raio, y - raio))
