import math
import random
from datetime import datetime

import utils.kivy_adapter as kivy_adapter
from utils.config import obter_hora_decimal


class CeuRenderer:
    def __init__(self, tela, largura, altura):
        self.tela = tela

        self.largura = largura
        self.altura = altura

        self.superficie = kivy_adapter.Surface((largura, self.altura))
        self.luz = kivy_adapter.Surface((largura, self.altura))

        random.seed(42)
        self.estrelas = []

        largura_celula = 90
        altura_celula = 55

        limite = int(self.altura * 0.85)
        for gy in range(15, limite, altura_celula):
            for gx in range(0, self.largura, largura_celula):
                quantidade = random.choices([0, 1, 2], weights=[30, 65, 5])[0]

                for _ in range(quantidade):
                    tipo = random.choices(["pequena", "brilho"], weights=[97, 3])[0]

                    self.estrelas.append(
                        {
                            "x": gx + random.randint(8, largura_celula - 8),
                            "y": gy + random.randint(8, altura_celula - 8),
                            "tipo": tipo,
                            "fase": random.random() * math.pi * 2,
                        }
                    )

    # =======================================================
    # INTERPOLAÇÃO
    # =======================================================
    def _lerp(self, a, b, t):
        return a + (b - a) * t

    def _lerp_cor(self, cor1, cor2, t):
        return (
            int(self._lerp(cor1[0], cor2[0], t)),
            int(self._lerp(cor1[1], cor2[1], t)),
            int(self._lerp(cor1[2], cor2[2], t)),
        )

    # =======================================================
    # CORES DO CÉU
    # =======================================================

    def obter_cores(self):
        # -------------------------
        # Madrugada
        # -------------------------
        if self.hora < 5:
            return (
                (5, 10, 35),
                (20, 30, 70),
            )

        # -------------------------
        # Nascer do Sol
        # -------------------------
        if self.hora < 7:
            t = (self.hora - 5) / 2

            topo = self._lerp_cor(
                (5, 10, 35),
                (90, 150, 255),
                t,
            )

            baixo = self._lerp_cor(
                (20, 30, 70),
                (255, 170, 90),
                t,
            )

            return topo, baixo

        # -------------------------
        # Manhã
        # -------------------------
        if self.hora < 11:
            t = (self.hora - 7) / 4

            topo = self._lerp_cor(
                (90, 150, 255),
                (70, 170, 255),
                t,
            )

            baixo = self._lerp_cor(
                (255, 170, 90),
                (180, 220, 255),
                t,
            )

            return topo, baixo

        # -------------------------
        # Meio-dia
        # -------------------------
        if self.hora < 15:
            return (
                (55, 165, 255),
                (180, 230, 255),
            )

        # -------------------------
        # Tarde
        # -------------------------
        if self.hora < 17:
            t = (self.hora - 15) / 2

            topo = self._lerp_cor(
                (55, 165, 255),
                (100, 120, 255),
                t,
            )

            baixo = self._lerp_cor(
                (180, 230, 255),
                (255, 195, 120),
                t,
            )

            return topo, baixo

        # -------------------------
        # Pôr do Sol
        # -------------------------
        if self.hora < 18:
            t = self.hora - 17

            topo = self._lerp_cor(
                (100, 120, 255),
                (45, 55, 140),
                t,
            )

            baixo = self._lerp_cor(
                (255, 195, 120),
                (255, 95, 60),
                t,
            )

            return topo, baixo

        # -------------------------
        # Crepúsculo
        # -------------------------
        if self.hora < 18.7:
            t = (self.hora - 18) / 0.7

            topo = self._lerp_cor(
                (45, 55, 140),
                (10, 15, 55),
                t,
            )

            baixo = self._lerp_cor(
                (255, 95, 60),
                (45, 35, 80),
                t,
            )

            return topo, baixo

        # -------------------------
        # Noite
        # -------------------------
        if self.hora < 22:
            t = (self.hora - 18.7) / 3.3

            topo = self._lerp_cor(
                (10, 15, 55),
                (5, 10, 35),
                t,
            )

            baixo = self._lerp_cor(
                (45, 35, 80),
                (20, 30, 70),
                t,
            )

            return topo, baixo

        return (
            (5, 10, 35),
            (20, 30, 70),
        )

    # =======================================================
    # DESENHA O DEGRADÊ
    # =======================================================
    def desenhar(self):
        self.hora = obter_hora_decimal()

        topo, baixo = self.obter_cores()

        for y in range(self.altura):
            t = y / self.altura
            cor = self._lerp_cor(topo, baixo, t)

            kivy_adapter.draw.line(
                self.superficie,
                cor,
                (0, y),
                (self.largura, y),
            )

        self.desenhar_luz()

        self.tela.blit(
            self.superficie,
            (0, 0),
        )

        self.tela.blit(
            self.luz,
            (0, 0),
        )

    def desenhar_luz(self):
        astro = self.obter_astro()

        self.luz.fill((0, 0, 0, 0))

        if astro["tipo"] == "lua":
            self.desenhar_estrelas()

        # ============================
        # Glow
        # ============================

        camadas = 30

        for i in range(camadas, 0, -1):
            fator = i / camadas

            if astro["tipo"] == "sol":
                raio = int(astro["raio"] + fator * 50)

                cor = (
                    255,
                    220,
                    120,
                    int(18 * fator * fator),
                )

            else:
                raio = int(astro["raio"] + fator * 24)

                cor = (
                    175,
                    205,
                    255,
                    int(14 * fator * fator),
                )

            kivy_adapter.draw.circle(
                self.luz,
                cor,
                (
                    astro["x"],
                    astro["y"],
                ),
                raio,
            )

        # ============================
        # Disco do Sol (degradê)
        # ============================

        if astro["tipo"] == "sol":
            raio = astro["raio"]

            for i in range(raio, 0, -1):
                fator = i / raio

                if astro["tipo"] == "sol":
                    cor = (
                        255,
                        int(210 + 45 * fator),
                        int(70 + 120 * fator),
                        255,
                    )

                else:
                    valor = int(200 + 40 * fator)

                    cor = (
                        valor,
                        valor,
                        255,
                        255,
                    )

                kivy_adapter.draw.circle(
                    self.luz,
                    cor,
                    (
                        astro["x"],
                        astro["y"],
                    ),
                    i,
                )

        if astro["tipo"] == "lua":
            lua = self.obter_fase_lua()

            self.desenhar_lua(
                astro["x"],
                astro["y"],
                astro["raio"],
                lua["fase"],
                lua["nome"],
            )

    def obter_astro(self):
        # ==========================================================
        # DIA (06:00 -> 18:00)
        # ==========================================================

        if 6 <= self.hora < 18:
            t = (self.hora - 6) / 12.0

            x = int(self.largura * (0.10 + 0.80 * t))

            y_inicio = int(self.altura * 0.95)
            y_topo = int(self.altura * 0.25)

            y = int(y_inicio - (y_inicio - y_topo) * (1 - (2 * t - 1) ** 2))

            if self.hora < 16:
                cor = (255, 225, 110)
            elif self.hora < 17:
                cor = (255, 175, 80)
            else:
                cor = (255, 120, 70)

            return {
                "tipo": "sol",
                "x": x,
                "y": y,
                "raio": 10,
                "cor": cor,
                "alpha": 40,
            }

        # ==========================================================
        # LUA (18:00 -> 06:00)
        # ==========================================================

        if self.hora >= 18:
            t = (self.hora - 18) / 12.0
        else:
            t = (self.hora + 6) / 12.0

        x = int(self.largura * (0.90 - 0.80 * t))

        y_inicio = int(self.altura * 0.98)
        y_topo = int(self.altura * 0.20)

        y = int(y_inicio - (y_inicio - y_topo) * (1 - (2 * t - 1) ** 2))

        raio = int(12 + 8 * abs(2 * t - 1))

        cor = (220, 225, 245)

        return {
            "tipo": "lua",
            "x": x,
            "y": y,
            "raio": raio,
            "cor": cor,
            "alpha": 30,
        }

    def obter_cor_ceu(self, y):
        topo, baixo = self.obter_cores()

        t = max(0, min(1, y / self.altura))

        return (
            int(self._lerp(topo[0], baixo[0], t)),
            int(self._lerp(topo[1], baixo[1], t)),
            int(self._lerp(topo[2], baixo[2], t)),
            255,
        )

    def obter_fase_lua(self):
        """
        Retorna informações da fase atual da Lua.

        ciclo:
            0.00 -> Lua Nova
            0.25 -> Quarto Crescente
            0.50 -> Lua Cheia
            0.75 -> Quarto Minguante
            1.00 -> Lua Nova novamente
        """

        # Lua Nova conhecida (06/01/2000 18:14 UTC)
        referencia = datetime(2000, 1, 6, 18, 14)

        agora = datetime.now()

        dias = (agora - referencia).total_seconds() / 86400.0

        ciclo_lunar = 29.530588853

        idade = dias % ciclo_lunar

        fase = idade / ciclo_lunar

        if fase < 0.03 or fase >= 0.97:
            nome = "nova"

        elif fase < 0.22:
            nome = "crescente"

        elif fase < 0.28:
            nome = "quarto_crescente"

        elif fase < 0.47:
            nome = "gibosa_crescente"

        elif fase < 0.53:
            nome = "cheia"

        elif fase < 0.72:
            nome = "gibosa_minguante"

        elif fase < 0.78:
            nome = "quarto_minguante"

        else:
            nome = "minguante"

        return {
            "fase": fase,  # valor entre 0 e 1
            "idade": idade,  # dias desde a Lua Nova
            "nome": nome,
        }

    def desenhar_lua(
        self,
        cx,
        cy,
        raio,
        fase,
        nome,
    ):
        import math

        # ----------------------------------------
        # Cor da lua
        # ----------------------------------------

        luz = (
            235,
            238,
            250,
            255,
        )

        # ----------------------------------------
        # Glow
        # ----------------------------------------

        for r in range(raio + 8, raio, -1):
            alpha = int(8 * ((r - raio) / 8))

            kivy_adapter.draw.circle(
                self.luz,
                (
                    175,
                    205,
                    255,
                    alpha,
                ),
                (
                    cx,
                    cy,
                ),
                r,
            )

        # ----------------------------------------
        # Lua Nova
        # ----------------------------------------

        if nome == "nova":
            return

        # ----------------------------------------
        # Calcula iluminação
        # ----------------------------------------

        if fase <= 0.5:
            iluminacao = fase / 0.5
            crescente = True

        else:
            iluminacao = (1.0 - fase) / 0.5
            crescente = False

        iluminacao = max(
            0.0,
            min(
                1.0,
                iluminacao,
            ),
        )

        # ----------------------------------------
        # Desenha linha por linha
        # ----------------------------------------

        for dy in range(-raio, raio + 1):
            largura_total = math.sqrt(raio * raio - dy * dy)

            largura_total = int(largura_total)

            if largura_total <= 0:
                continue

            # ----------------------------
            # Lua cheia
            # ----------------------------

            if nome == "cheia":
                x1 = -largura_total
                x2 = largura_total

            # ----------------------------
            # Quarto Crescente
            # ----------------------------

            elif nome == "quarto_crescente":
                x1 = 0
                x2 = largura_total

            # ----------------------------
            # Quarto Minguante
            # ----------------------------

            elif nome == "quarto_minguante":
                x1 = -largura_total
                x2 = 0

            elif nome == "gibosa_crescente":
                largura_iluminada = int(largura_total * iluminacao)

                t = (fase - 0.28) / (0.47 - 0.28)

                excesso = int(largura_total * (0.10 + 0.17 * t))

                x1 = largura_total - largura_iluminada - excesso
                x2 = largura_total

            # ----------------------------
            # Restantes
            # ----------------------------

            else:
                largura_iluminada = int(largura_total * iluminacao)

                if crescente:
                    x1 = largura_total - largura_iluminada
                    x2 = largura_total

                else:
                    x1 = -largura_total
                    x2 = -largura_total + largura_iluminada

            if x2 <= x1:
                continue

            kivy_adapter.draw.line(
                self.luz,
                luz,
                (
                    cx + x1,
                    cy + dy,
                ),
                (
                    cx + x2,
                    cy + dy,
                ),
            )

        # ----------------------------------------
        # Borda suave
        # ----------------------------------------

        kivy_adapter.draw.circle(
            self.luz,
            (
                245,
                248,
                255,
                80,
            ),
            (
                cx,
                cy,
            ),
            raio,
            1,
        )

    def desenhar_estrelas(self):
        if 6 <= self.hora < 18:
            return

        brilho_noite = 1.0

        if self.hora < 20:
            brilho_noite = (self.hora - 18) / 2

        elif self.hora > 4:
            brilho_noite = (6 - self.hora) / 2

        brilho_noite = max(0, min(1, brilho_noite))

        tempo = datetime.now().timestamp()

        for estrela in self.estrelas:
            astro = self.obter_astro()

            dx = estrela["x"] - astro["x"]
            dy = estrela["y"] - astro["y"]

            if dx * dx + dy * dy < 90 * 90:
                continue

            brilho = 180 + int(75 * math.sin(tempo * 1.5 + estrela["fase"]))

            cor = (
                brilho,
                brilho,
                brilho,
                255,
            )

            if estrela["tipo"] == "pequena":
                kivy_adapter.draw.circle(
                    self.luz,
                    cor,
                    (
                        estrela["x"],
                        estrela["y"],
                    ),
                    1,
                )
            else:
                x = estrela["x"]
                y = estrela["y"]

                for r in range(4, 0, -1):
                    kivy_adapter.draw.circle(
                        self.luz,
                        (
                            brilho,
                            brilho,
                            brilho,
                            15,
                        ),
                        (x, y),
                        r,
                    )

                kivy_adapter.draw.circle(
                    self.luz,
                    cor,
                    (x, y),
                    1,
                )
