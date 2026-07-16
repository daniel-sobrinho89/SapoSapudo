import math
import random
from datetime import datetime

import kivy_adapter
from render.asset_manager import asset_manager


class BackgroundRenderer:
    def __init__(self, tela, largura, altura, transform, clima_service, ambiente):
        self.tela = tela
        self.transform = transform
        self.clima_service = clima_service
        self.ambiente = ambiente
        self.ceu_renderer = CeuRenderer(
            tela,
            largura,
            ambiente,
        )
        self.horizonte_renderer = HorizonteRenderer(tela, largura, transform)
        self.chao_renderer = ChaoRenderer(tela, largura, altura, transform)
        # =====================================
        # BACKGROUND MANHÃ
        # =====================================

        background_manha = asset_manager.carregar("background_manha.webp")

        self.background_manha = self.transform.escalar(
            background_manha, (largura, altura)
        )

        # =====================================
        # BACKGROUND DIA
        # =====================================

        background_day = asset_manager.carregar("background.webp")

        self.background_day = self.transform.escalar(background_day, (largura, altura))

        # =====================================
        # BACKGROUND FINAL TARDE
        # =====================================

        background_final_tarde = asset_manager.carregar("background_final_tarde.webp")

        self.background_final_tarde = self.transform.escalar(
            background_final_tarde, (largura, altura)
        )

        # =====================================
        # BACKGROUND NOITE
        # =====================================

        background_night = asset_manager.carregar("background_night_19h.webp")

        self.background_night = self.transform.escalar(
            background_night, (largura, altura)
        )

        # =====================================
        # FEIRA MANHÃ
        # =====================================

        background_feira_manha = asset_manager.carregar("background_feira_manha.webp")

        self.background_feira_manha = self.transform.escalar(
            background_feira_manha, (largura, altura)
        )

        # =====================================
        # FEIRA DIA
        # =====================================

        background_feira = asset_manager.carregar("background_feira.webp")

        self.background_feira = self.transform.escalar(
            background_feira, (largura, altura)
        )

        # =====================================
        # FEIRA FINAL TARDE
        # =====================================

        background_feira_final_tarde = asset_manager.carregar(
            "background_feira_final_tarde.webp"
        )

        self.background_feira_final_tarde = self.transform.escalar(
            background_feira_final_tarde, (largura, altura)
        )

        # =====================================
        # FEIRA NOITE
        # =====================================

        background_feira_night = asset_manager.carregar(
            "background_feira_night_19h.webp"
        )

        self.background_feira_night = self.transform.escalar(
            background_feira_night, (largura, altura)
        )

        # =====================================
        # CHUVA
        # =====================================

        background_chuva = asset_manager.carregar("background_chuva.webp")

        self.background_chuva = self.transform.escalar(
            background_chuva, (largura, altura)
        )

        background_feira_chuva = asset_manager.carregar("background_feira_chuva.webp")

        self.background_feira_chuva = self.transform.escalar(
            background_feira_chuva, (largura, altura)
        )

        self.cenario_feira = False

    def obter_background_atual(self):
        if self.cenario_feira:
            return self.obter_background_feira()

        hora_atual = self.ambiente.obter_hora_decimal()

        if self.esta_chovendo() and not (hora_atual >= 18.5 or hora_atual < 6):
            return self.background_chuva

        # =====================================
        # MANHÃ
        # =====================================

        if 6 <= hora_atual < 12:
            return self.background_manha

        # =====================================
        # FINAL TARDE
        # =====================================

        if 15 <= hora_atual < 18.5:
            return self.background_final_tarde

        # =====================================
        # NOITE
        # =====================================

        if hora_atual >= 18.5 or hora_atual < 6:
            return self.background_night

        # =====================================
        # DIA
        # =====================================

        return self.background_day

    def obter_background_feira(self):
        if self.esta_chovendo():
            return self.background_feira_chuva

        hora_atual = self.ambiente.obter_hora_decimal()

        if 6 <= hora_atual < 12:
            return self.background_feira_manha

        if 15 <= hora_atual < 18.5:
            return self.background_feira_final_tarde

        if hora_atual >= 18.5 or hora_atual < 6:
            return self.background_feira_night

        return self.background_feira

    def eh_dia(self):
        return self.ambiente.eh_dia()

    def esta_chovendo(self):
        return self.ambiente.esta_chovendo(self.clima_service)

    def desenhar(self):
        # background = self.obter_background_atual()
        # self.tela.blit(background, (0, 0))

        self.ceu_renderer.desenhar()
        self.horizonte_renderer.desenhar()
        self.chao_renderer.desenhar()


class CeuRenderer:
    def __init__(self, tela, largura, ambiente):
        self.tela = tela
        self.ambiente = ambiente

        self.largura = largura
        self.altura = 425

        self.superficie = kivy_adapter.Surface((largura, self.altura))
        self.luz = kivy_adapter.Surface((largura, self.altura))

        random.seed(42)
        self.estrelas = []

        largura_celula = 90
        altura_celula = 55

        for gy in range(15, 250, altura_celula):
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
        if self.hora < 19:
            t = (self.hora - 17) / 2

            topo = self._lerp_cor(
                (100, 120, 255),
                (20, 35, 90),
                t,
            )

            baixo = self._lerp_cor(
                (255, 195, 120),
                (255, 110, 70),
                t,
            )

            return topo, baixo

        # -------------------------
        # Noite
        # -------------------------
        if self.hora < 22:
            t = (self.hora - 19) / 3

            topo = self._lerp_cor(
                (20, 35, 90),
                (5, 10, 35),
                t,
            )

            baixo = self._lerp_cor(
                (255, 110, 70),
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
        self.hora = self.ambiente.obter_hora_decimal()

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
            )

    def obter_astro(self):
        # ==========================================================
        # DIA (06:00 -> 18:00)
        # ==========================================================

        if 6 <= self.hora < 18:
            t = (self.hora - 6) / 12.0

            x = int(self.largura * (0.10 + 0.80 * t))

            y_inicio = 310
            y_topo = 120

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

        y_inicio = 340
        y_topo = 90

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
    ):
        topo, _ = self.obter_cores()

        sombra = (
            topo[0] + 6,
            topo[1] + 6,
            topo[2] + 8,
            255,
        )

        luz = (
            235,
            238,
            250,
            255,
        )

        # disco iluminado
        kivy_adapter.draw.circle(
            self.luz,
            luz,
            (cx, cy),
            raio,
        )

        # lua cheia
        if 0.48 <= fase <= 0.52:
            return

        # lua nova
        if fase < 0.02 or fase > 0.98:
            kivy_adapter.draw.circle(
                self.luz,
                sombra,
                (cx, cy),
                raio,
            )

            return

        if fase < 0.5:
            t = fase / 0.5

            deslocamento = int(self._lerp(-raio, raio, t))

        else:
            t = (fase - 0.5) / 0.5

            deslocamento = int(self._lerp(raio, -raio, t))

        kivy_adapter.draw.circle(
            self.luz,
            sombra,
            (
                cx + deslocamento,
                cy,
            ),
            raio,
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


class HorizonteRenderer:
    def __init__(self, tela, largura_tela, transform):
        self.tela = tela

        imagem = asset_manager.carregar("background/horizonte.webp")

        # O horizonte ocupa 90% da largura da tela
        self.largura = int(largura_tela * 0.90)

        proporcao = imagem.get_height() / imagem.get_width()

        self.altura = int(self.largura * proporcao)

        self.horizonte = transform.escalar(
            imagem,
            (
                self.largura,
                self.altura,
            ),
        )

        self.x = (largura_tela - self.largura) // 2
        self.y = 310

    def desenhar(self):
        self.tela.blit(
            self.horizonte,
            (
                self.x,
                self.y,
            ),
        )


class ChaoRenderer:
    def __init__(self, tela, largura, altura, transform):
        self.tela = tela

        imagem = asset_manager.carregar("background/chao.webp")

        self.altura = 220

        self.chao = transform.escalar(
            imagem,
            (largura, self.altura),
        )

        self.y = altura - self.altura

    def desenhar(self):
        self.tela.blit(
            self.chao,
            (0, self.y),
        )
