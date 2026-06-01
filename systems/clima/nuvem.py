# ==========================================
# nuvem.py
# ==========================================

import pygame
import random
import math

from pathlib import Path


class Nuvem:

    # cache global
    sprites = None
    sprites_flip = None

    cache_escalas = {}
    cache_alpha = {}


    OUTSIDE_DISTANCE = 1
    SPEED_MIN = 5
    SPEED_MAX = 12

    def __init__(
        self,
        area,
        intensidade=1,
        wind_direction=0,
        wind_speed=0
    ):

        # =====================================
        # LOAD SPRITES
        # =====================================

        if Nuvem.sprites is None:

            asset_path = Path("assets/clima")

            nuvem_1 = pygame.image.load(
                asset_path / "nuvem_1.png"
            ).convert_alpha()

            nuvem_2 = pygame.image.load(
                asset_path / "nuvem_2.png"
            ).convert_alpha()

            Nuvem.sprites = [
                nuvem_1,
                nuvem_2
            ]

            Nuvem.sprites_flip = [
                pygame.transform.flip(
                    nuvem_1,
                    True,
                    False
                ),
                pygame.transform.flip(
                    nuvem_2,
                    True,
                    False
                )
            ]

        # =====================================
        # SPRITE
        # =====================================

        indice = random.randint(0, 1)

        if random.random() > 0.5:

            self.sprite_original = (
                Nuvem.sprites_flip[indice]
            )

        else:

            self.sprite_original = (
                Nuvem.sprites[indice]
            )

        # =====================================
        # AREA
        # =====================================

        self.area = area

        self.intensidade = intensidade
        self.wind_direction = wind_direction
        self.wind_speed = wind_speed

        # =====================================
        # ESCALA
        # =====================================

        self.escala = random.uniform(
            0.10,
            0.28
        ) * max(0.4, intensidade)

        # =====================================
        # POSIÇÃO
        # =====================================

        self.sprite = (
            self.obter_sprite_escalado(
                self.sprite_original,
                self.escala
            )
        )

        self.width = self.sprite.get_width()
        self.height = self.sprite.get_height()

        direcao_destino = (
            wind_direction + 180
        ) % 360

        vento_vai_para_direita = (
            0 <= direcao_destino < 180
        )

        self.start_side = (
            "left"
            if vento_vai_para_direita
            else "right"
        )

        fator_vento = max(
            0.5,
            min(
                3.0,
                wind_speed / 10
            )
        )

        velocidade_base = (
            random.uniform(
                Nuvem.SPEED_MIN,
                Nuvem.SPEED_MAX
            )
            * fator_vento
        )

        if self.start_side == "left":

            self.vx = velocidade_base

            self.x = random.uniform(
                self.area.left - self.width,
                self.area.left + self.area.width * 0.25
            )

        else:

            self.vx = -velocidade_base

            self.x = random.uniform(
                self.area.right + self.width,
                self.area.right - self.area.width * 0.25
            )

        self.base_y = random.uniform(
            self.area.top + self.height,
            self.area.bottom - self.height
        )

        self.y = self.base_y

        # =====================================
        # BEHAVIOR
        # =====================================

        self.behavior = random.choices(
            [
                "straight",
                "vanish_midway"
            ],
            weights=[8, 2],
            k=1
        )[0]

        self.bounced = False
        self.dying = False
        self.fade_speed = random.uniform(40, 80)

        if self.behavior == "pingpong_disappear":
            if self.start_side == "left":
                self.return_target = self.area.left + self.area.width * 0.08
            else:
                self.return_target = self.area.right - self.area.width * 0.08

        if self.behavior == "vanish_midway":
            if self.start_side == "left":
                self.vanish_x = random.uniform(
                    self.area.left + self.width,
                    self.area.right - self.width * 2
                )
            else:
                self.vanish_x = random.uniform(
                    self.area.right - self.width,
                    self.area.left + self.width * 2
                )

        # =====================================
        # MOVIMENTO FLUTUANTE
        # =====================================

        self.offset = random.uniform(0, 100)
        self.float_amplitude = random.uniform(2, 6)

        # =====================================
        # ALPHA
        # =====================================

        self.alpha = random.randint(
            18,
            45
        )

    # ==========================================
    # UPDATE
    # ==========================================

    def atualizar(self, dt):

        if self.dying:
            self.alpha = max(0, self.alpha - self.fade_speed * dt)
            return self.alpha > 0

        self.x += self.vx * dt

        # movimento flutuante vertical
        self.y = self.base_y + math.sin(
            pygame.time.get_ticks() * 0.00035
            + self.offset
        ) * self.float_amplitude

        if self.behavior == "straight":
            if self.vx > 0 and self.x > self.area.right + Nuvem.OUTSIDE_DISTANCE:
                self.dying = True
            elif self.vx < 0 and self.x < self.area.left - Nuvem.OUTSIDE_DISTANCE:
                self.dying = True

        elif self.behavior == "pingpong_disappear":
            if not self.bounced:
                far_edge = self.area.right + Nuvem.OUTSIDE_DISTANCE if self.vx > 0 else self.area.left - Nuvem.OUTSIDE_DISTANCE
                if (self.vx > 0 and self.x >= far_edge) or (self.vx < 0 and self.x <= far_edge):
                    self.vx = -self.vx * 0.8
                    self.bounced = True
            else:
                if (self.vx < 0 and self.x <= self.return_target) or (self.vx > 0 and self.x >= self.return_target):
                    self.dying = True

        elif self.behavior == "back_and_forth_then_die":
            if not self.bounced:
                far_edge = self.area.right + Nuvem.OUTSIDE_DISTANCE if self.vx > 0 else self.area.left - Nuvem.OUTSIDE_DISTANCE
                if (self.vx > 0 and self.x >= far_edge) or (self.vx < 0 and self.x <= far_edge):
                    self.vx = -self.vx * 0.85
                    self.bounced = True
            else:
                opposite_edge = self.area.left - Nuvem.OUTSIDE_DISTANCE if self.vx < 0 else self.area.right + Nuvem.OUTSIDE_DISTANCE
                if (self.vx > 0 and self.x >= opposite_edge) or (self.vx < 0 and self.x <= opposite_edge):
                    self.dying = True

        elif self.behavior == "vanish_midway":
            if (self.vx > 0 and self.x >= self.vanish_x) or (self.vx < 0 and self.x <= self.vanish_x):
                self.dying = True

        return self.alpha > 0

    # ==========================================
    # RENDER
    # ==========================================

    def renderizar(
        self,
        tela,
        eh_dia=False
    ):

        alpha_final = self.alpha

        if eh_dia:

            alpha_final *= 2.2

        alpha_final = min(
            255,
            int(alpha_final)
        )

        sprite = self.obter_sprite_alpha(
            self.sprite,
            alpha_final
        )

        rect = sprite.get_rect(
            center=(int(self.x), int(self.y))
        )

        tela.blit(
            sprite,
            rect
        )


    # ==========================================
    # HELPERS
    # ==========================================

    @classmethod
    def obter_sprite_escalado(
        cls,
        sprite,
        escala
    ):
        chave = (
            id(sprite),
            round(escala, 3)
        )

        if chave not in cls.cache_escalas:

            largura = max(
                8,
                int(sprite.get_width() * escala)
            )

            altura = max(
                8,
                int(sprite.get_height() * escala)
            )

            cls.cache_escalas[chave] = (
                pygame.transform.smoothscale(
                    sprite,
                    (largura, altura)
                ).convert_alpha()
            )

        return cls.cache_escalas[chave]

    @classmethod
    def obter_sprite_alpha(
        cls,
        sprite,
        alpha
    ):

        chave = (
            id(sprite),
            alpha
        )

        if chave not in cls.cache_alpha:

            copia = sprite.copy()

            copia.set_alpha(alpha)

            cls.cache_alpha[chave] = copia

        return cls.cache_alpha[chave]