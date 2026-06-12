# ==========================================
# nuvem.py
# ==========================================

import random
import math
from systems.fisica import sistema_fisica
import threading
import pygame_adapter

class Nuvem:
    # cache global
    sprites = None
    sprites_flip = None

    carregando = False
    carregado = False
    raw_sprites = None
    raw_prontos = False
    sprites_convertidos = 0

    cache_escalas = {}
    cache_alpha = {}

    OUTSIDE_DISTANCE = 50
    SPEED_MIN = 1
    SPEED_MAX = 5

    def __init__(
        self,
        area,
        transform,
        intensidade=1,
        wind_direction=0,
        wind_speed=0,
        ceu_limpo=False
    ):
        self.transform = transform
        self.tempo = random.uniform(0, 100)
        self.ceu_limpo = ceu_limpo

        # =====================================
        # SPRITE
        # =====================================

        self.frame_animacao = random.randint(
            0,
            max(
                0,
                len(Nuvem.sprites) - 1
            )
        )

        self.velocidade_animacao = random.uniform(
            0.5,
            0.9
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

        if self.ceu_limpo:
            self.escala = random.uniform(
                0.7,
                1.0
            )
        else:
            self.escala = random.uniform(
                0.9,
                1.4
            ) * max(0.4, intensidade)

        # =====================================
        # POSIÇÃO
        # =====================================

        sprite_referencia = Nuvem.sprites[0]

        self.width = int(
            sprite_referencia.get_width()
            * self.escala
        )

        self.height = int(
            sprite_referencia.get_height()
            * self.escala
        )

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
                -80,
                -30
            )
        else:
            self.vx = -velocidade_base
            self.x = random.uniform(
                self.area.right + 30,
                self.area.right + 80
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
        self.float_amplitude = random.uniform(
            4,
            12
        )

        # =====================================
        # ALPHA
        # =====================================

        # tornar nuvens menos transparentes (mais visíveis)
        if self.ceu_limpo:
            self.alpha = random.randint(
                60,
                80
            )
        else:
            self.alpha = random.randint(
                80,
                100
            )

    @classmethod
    def iniciar_carregamento(cls):
        if cls.carregando or cls.carregado:
            return

        cls.carregando = True

        def worker():
            try:
                from render.asset_manager import asset_manager
                raw_sprites = []

                for i in range(48):

                    raw = asset_manager.carregar_raw(
                        f"clima/nuvens/nuvem_{i:04d}.webp"
                    )

                    raw_sprites.append(raw)

                cls.raw_sprites = raw_sprites
                cls.raw_prontos = True
            finally:
                cls.carregando = False

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    # ==========================================
    # UPDATE
    # ==========================================

    @classmethod
    def finalizar_carregamento(cls):

        if (
            not cls.raw_prontos
            or cls.carregado
        ):
            return

        if cls.sprites is None:
            cls.sprites = []

        for _ in range(5):  # converte 5 por frame
            if cls.sprites_convertidos >= len(cls.raw_sprites):
                cls.raw_sprites = None
                cls.raw_prontos = False
                cls.carregado = True

                return

            raw = cls.raw_sprites[
                cls.sprites_convertidos
            ]

            sprite = pygame_adapter.image.from_raw(
                raw
            )
            cls.sprites.append(
                sprite.convert_alpha()
            )
            cls.sprites_convertidos += 1

    def atualizar(self, dt):
        if not Nuvem.sprites:
            return True

        self.tempo += dt

        self.frame_animacao += (
            self.velocidade_animacao * dt
        )

        if self.frame_animacao >= len(Nuvem.sprites):
            self.frame_animacao -= len(
                Nuvem.sprites
            )

        if self.dying:
            self.alpha = max(0, self.alpha - self.fade_speed * dt)
            return self.alpha > 0

        # aplicar força do vento centralizado apenas se a nuvem estiver fora da área do frasco
        if not self.area.collidepoint(int(self.x), int(self.y)):
            sistema_fisica.aplicar_forca_vento(self, None, dt, sensibilidade=self.escala)

        self.x += self.vx * dt

        # movimento flutuante vertical
        self.y = self.base_y + math.sin(
            self.tempo * 0.35
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
        if not Nuvem.sprites:
            return

        indice = int(
            self.frame_animacao
        )

        sprite_base = (
            Nuvem.sprites[indice]
        )

        alpha_final = self.alpha

        if eh_dia:

            alpha_final *= 2.2

        alpha_final = min(
            255,
            int(alpha_final)
        )

        sprite_escalado = (
            self.obter_sprite_escalado(
                sprite_base,
                self.escala,
                self.transform
            )
        )

        sprite = self.obter_sprite_alpha(
            sprite_escalado,
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
        escala,
        transform
    ):

        largura = max(
            8,
            round(sprite.get_width() * escala)
        )

        altura = max(
            8,
            round(sprite.get_height() * escala)
        )

        chave = (
            id(sprite),
            largura,
            altura
        )

        if chave not in cls.cache_escalas:

            if len(cls.cache_escalas) > 200:
                cls.cache_escalas.clear()

            sprite_escalado = transform.escalar_nuvem(
                sprite,
                (
                    largura,
                    altura
                )
            )

            sprite_escalado = (
                sprite_escalado.convert_alpha()
            )

            cls.cache_escalas[chave] = (
                sprite_escalado
            )

        return cls.cache_escalas[chave]

    @classmethod
    def obter_sprite_alpha(
        cls,
        sprite,
        alpha
    ):
        alpha = int(alpha / 10) * 10
        chave = (
            id(sprite),
            alpha
        )

        if chave not in cls.cache_alpha:

            copia = sprite.copy()
            copia.set_alpha(alpha)

            if len(cls.cache_alpha) > 500:
                cls.cache_alpha.clear()

            cls.cache_alpha[chave] = copia

        return cls.cache_alpha[chave]