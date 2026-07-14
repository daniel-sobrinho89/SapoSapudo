import math
import random

import kivy_adapter
from core.event_bus import event_bus
from render.asset_manager import asset_manager


class CasaDuende:
    def __init__(self, transform):
        self.transform = transform
        self.x = 140
        self.y = 190
        self.escala = 0.13
        self.escala_x = 6.0
        self.escala_y = 6.0
        self.offset_casa_y = 0
        self.offset_casa_x = -6

        # =====================================
        # LOAD IMAGENS
        # =====================================

        casa_duende_apagada = asset_manager.carregar(
            "casa_duende/casa_duende_apagada.webp"
        )
        casa_duende_janela_superior_aberta = asset_manager.carregar(
            "casa_duende/casa_duende_janela_superior_aberta.webp"
        )

        # =====================================
        # REMOVE ESPAÇOS TRANSPARENTES
        # =====================================

        casa_duende_crop = casa_duende_apagada.subsurface(
            casa_duende_apagada.get_bounding_rect()
        ).copy()

        casa_duende_janela_superior_aberta_crop = (
            casa_duende_janela_superior_aberta.subsurface(
                casa_duende_janela_superior_aberta.get_bounding_rect()
            ).copy()
        )

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

        # =====================================
        # CASA
        # =====================================

        self.casa_duende_apagada = self.transform.escalar(
            casa_duende_crop,
            (
                int(casa_duende_crop.get_width() * self.escala * self.escala_x),
                int(casa_duende_crop.get_height() * self.escala * self.escala_y),
            ),
        )

        self.casa_duende_janela_superior_aberta = self.transform.escalar(
            casa_duende_janela_superior_aberta_crop,
            (
                int(
                    casa_duende_janela_superior_aberta_crop.get_width()
                    * self.escala
                    * self.escala_x
                ),
                int(
                    casa_duende_janela_superior_aberta_crop.get_height()
                    * self.escala
                    * self.escala_y
                ),
            ),
        )

        self.casa_duende = self.casa_duende_apagada
        # =====================================
        # TAMANHO FINAL DA CASA
        # =====================================

        self.largura = self.casa_duende.get_width()

        # =====================================
        # POSICIONAMENTO AUTOMÁTICO
        # =====================================

        centro_x = self.largura // 2

        # =====================================
        # CASA
        # =====================================

        topo_casa = int(110 * self.escala / 0.13)

        casa_x = centro_x - self.casa_duende.get_width() // 2 + self.offset_casa_x
        casa_y = topo_casa + self.offset_casa_y

        self.casa_x = casa_x
        self.casa_y = casa_y
        self.altura = casa_y + self.casa_duende.get_height()

        # =====================================
        # SURFACE FINAL
        # =====================================

        self.casa_surface = kivy_adapter.Surface(
            (self.largura, self.altura), kivy_adapter.SRCALPHA
        )

        # =====================================
        # BLITS
        # =====================================

        self.casa_surface.blit(self.casa_duende, (casa_x, casa_y))

        # =====================================
        # ÁREA INTERNA
        # =====================================

        self.area_interna_offset_x = casa_x + int(self.casa_duende.get_width() * 0.10)

        self.area_interna_offset_y = casa_y + int(self.casa_duende.get_height() * 0.24)

        self.area_interna_width = int(self.casa_duende.get_width() * 0.80)

        self.area_interna_height = int(self.casa_duende.get_height() * 0.62)

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
            self.casa_surface.get_height() - 180,
        )

        # =====================================
        # ÁREA PROTEGIDA DA CASA
        # =====================================

        casa_x = self.x + casa_x + int(self.casa_duende.get_width() * 0.18)
        casa_y = self.y + casa_y + int(self.casa_duende.get_height() * 0.10)
        casa_w = int(self.casa_duende.get_width() * 0.67)
        casa_h = int(self.casa_duende.get_height() * 0.50)

        self.area_casa = kivy_adapter.Rect(casa_x, casa_y, casa_w, casa_h)

        event_bus.assinar("voo_iniciado", self.fechar_janela_superior)

    def atualizar(self, dt):
        self.tempo_nevoa += dt

    # =====================================
    # RENDER
    # =====================================

    def atualizar_posicao(self, centro_y=None):
        if centro_y is not None:
            base_offset = 100

            desired_bottom = centro_y + base_offset

            self.y = int(desired_bottom - self.altura)

            self.area_interna.x = self.x + self.area_interna_offset_x

            self.area_interna.y = self.y + self.area_interna_offset_y

            self.area_particulas.x = self.x + 40

            self.area_particulas.y = self.y + 40

            self.area_casa.x = (
                self.x
                + self.area_interna_offset_x
                + int(self.area_interna.width * 0.10)
            )

            self.area_casa.y = (
                self.y
                + self.area_interna_offset_y
                - int(self.casa_duende.get_height() * 0.07)
            )

    def abrir_janela_superior(self):
        self.casa_duende = self.casa_duende_janela_superior_aberta
        self._reconstruir_casa()

    def fechar_janela_superior(self, _evento=None):
        self.casa_duende = self.casa_duende_apagada
        self._reconstruir_casa()

    def _reconstruir_casa(self):
        self.casa_surface = kivy_adapter.Surface(
            (self.largura, self.altura),
            kivy_adapter.SRCALPHA,
        )

        self.casa_surface.blit(
            self.casa_duende,
            (self.casa_x, self.casa_y),
        )

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, tela, centro_y=None):
        self.atualizar_posicao(centro_y)
        tela.blit(self.casa_surface, (self.x, self.y))

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
