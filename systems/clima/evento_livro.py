# ==========================================
# evento_livro.py
# ==========================================

import math
import random
from systems.clima.livro_climatico import LivroClimatico
import kivy_adapter

class EventoLivro:

    def __init__(
        self,
        assets,
        transform
    ):
        self.assets = assets
        self.nevoa = 0.0
        self.tempo_sem_clique = 0.0
        self.livro_visivel = False
        self.timer_livro = 0.0
        self.tempo = 0.0
        self.x = 0
        self.y = 0
        self.rect_livro = None
        self.acumulador_retorno = 0.0
        self.livro_aberto_visivel = False
        self.livro_climatico = LivroClimatico()
        self.pagina_atual = None

        self.livro_fechado = assets.carregar(
            "clima/livro_fechado.webp"
        )

        self.livro_fechado = transform.escalar(
            self.livro_fechado,
            (
                int(self.livro_fechado.get_width() * 0.25),
                int(self.livro_fechado.get_height() * 0.25)
            )
        )

        self.livro_aberto = assets.carregar(
            "clima/livro_aberto.webp"
        )

        self.livro_aberto = transform.escalar(
            self.livro_aberto,
            (
                int(self.livro_aberto.get_width() * 1.10),
                int(self.livro_aberto.get_height() * 0.80)
            )
        )

        self.texto_livro = TextoLivro()


    def registrar_clique_poeira(self):
        self.tempo_sem_clique = 0
        self.acumulador_retorno = 0.0
        clicadas = sum(
            1
            for p in self.particulas
            if not p.ativa
        )
        total = len(self.particulas)
        self.nevoa = (
            clicadas / total
        ) * 7
        if clicadas >= total:
            self.mostrar_livro()

    def atualizar(self, dt):
        self.tempo += dt

        if self.livro_visivel:
            self.timer_livro -= dt
            if self.timer_livro <= 0:
                self.ocultar_livro_por_timeout()

            return
        
        self.tempo_sem_clique += dt

        if self.tempo_sem_clique > 5:
            self.acumulador_retorno += dt

            if self.acumulador_retorno >= 1.0:
                self.acumulador_retorno = 0.0
                self.restaurar_uma_poeira()

        self.nevoa = max(0, self.nevoa)


    def mostrar_livro(self):
        self.nevoa = 0
        self.tempo_sem_clique = 0
        self.acumulador_retorno = 0.0
        self.livro_visivel = True
        self.timer_livro = 420

    def ocultar_livro_por_clique(self):
        self.livro_visivel = False
        self.livro_aberto_visivel = True
        self.pagina_atual = None
        self.rect_livro = None
        self.nevoa = 0
        self.acumulador_retorno = 0.0
        self.tempo_sem_clique = 0
        for particula in self.particulas:
            particula.resetar()
            particula.ativa = True

    def ocultar_livro_por_timeout(self):
        self.livro_visivel = False
        self.rect_livro = None
        self.nevoa = 0
        self.acumulador_retorno = 0.0
        self.tempo_sem_clique = 0
        for particula in self.particulas:
            particula.resetar()
            particula.ativa = True

    def restaurar_uma_poeira(self):
        poeiras_ocultas = [
            p
            for p in self.particulas
            if not p.ativa
        ]

        if not poeiras_ocultas:
            return

        particula = random.choice(
            poeiras_ocultas
        )

        particula.resetar()
        particula.ativa = True

        clicadas = sum(
            1
            for p in self.particulas
            if not p.ativa
        )

        total = len(self.particulas)

        self.nevoa = (
            clicadas / total
        ) * 7

    def fechar_livro_aberto(self):
        self.livro_aberto_visivel = False
        self.pagina_atual = None
        self.nevoa = 0
        self.acumulador_retorno = 0.0
        self.tempo_sem_clique = 0

        for particula in self.particulas:
            particula.resetar()
            particula.ativa = True

    def renderizar_livro_aberto(
        self,
        tela, 
        clima_service
    ):
        if not self.livro_aberto_visivel:
            return

        largura = self.livro_aberto.get_width()
        altura = self.livro_aberto.get_height()

        largura_tela = tela.get_width()
        altura_tela = tela.get_height()

        x = (
            largura_tela // 2
            - largura // 2
        )

        y = (
            altura_tela // 2
            - altura // 2
        )

        tela.blit(
            self.livro_aberto,
            (
                x,
                y
            )
        )

        if self.pagina_atual is None:
            self.pagina_atual = (
                self.livro_climatico.gerar_pagina(
                    clima_service
                )
            )

        pagina = self.pagina_atual

        # ==========================
        # PÁGINA ESQUERDA
        # ==========================

        pagina_esquerda = (
            pagina["pagina_esquerda"]
        )

        texto_x = x + 240
        texto_y = y + 80

        self.texto_livro.desenhar(
            tela,
            pagina_esquerda["titulo"],
            texto_x,
            texto_y,
            titulo=True
        )

        texto_x_esquerda = x + 180
        texto_y = y + 150

        for linha in pagina_esquerda["linhas"]:
            partes = self.texto_livro.quebrar_texto(linha, 40)
            for parte in partes:
                self.texto_livro.desenhar(
                    tela,
                    parte,
                    texto_x_esquerda,
                    texto_y
                )
                texto_y += 24

            texto_y += 8

        # ==========================
        # PÁGINA DIREITA
        # ==========================

        pagina_direita = (
            pagina["pagina_direita"]
        )

        texto_x = x + 650
        texto_y = y + 80

        self.texto_livro.desenhar(
            tela,
            pagina_direita["titulo"],
            texto_x,
            texto_y,
            titulo=True
        )

        texto_x_direita = x + 600
        texto_y = y + 150

        for linha in pagina_direita["linhas"]:
            partes = self.texto_livro.quebrar_texto(linha, 40)
            for parte in partes:
                self.texto_livro.desenhar(
                    tela,
                    parte,
                    texto_x_direita,
                    texto_y
                )
                texto_y += 24

            texto_y += 8

        self.rect_livro_aberto = kivy_adapter.Rect(
            x,
            y,
            largura,
            altura
        )

    def renderizar(
        self,
        tela,
        frasco_climatico
    ):
        if not self.livro_visivel:
            return
        
        self.x = (frasco_climatico.area_pote.centerx)
        self.y = (frasco_climatico.area_pote.centery)

        self.offset_flutuacao = (
            math.sin(self.tempo * 2)
            * 5
        )

        y_final = (
            self.y
            + self.offset_flutuacao
        )

        largura = self.livro_fechado.get_width()
        altura = self.livro_fechado.get_height()

        x_final = self.x - largura // 2

        y_final = int(
            y_final - altura // 2
        )

        tela.blit(
            self.livro_fechado,
            (
                x_final,
                y_final
            )
        )

        self.rect_livro = kivy_adapter.Rect(
            x_final,
            y_final,
            largura,
            altura
        )

from PIL import ImageFont
from PIL import ImageDraw
import textwrap

class TextoLivro:

    def __init__(self):

        self.fonte_titulo = ImageFont.truetype(
            "assets/fonts/CormorantGaramond-Bold.ttf",
            35
        )

        self.fonte_texto = ImageFont.truetype(
            "assets/fonts/CormorantGaramond-Regular.ttf",
            20
        )

    def quebrar_texto(
        self,
        texto,
        largura=24
    ):

        return textwrap.wrap(
            texto,
            width=largura
        )

    def desenhar(
        self,
        surface,
        texto,
        x,
        y,
        titulo=False
    ):

        draw = ImageDraw.Draw(
            surface._img
        )

        fonte = (
            self.fonte_titulo
            if titulo
            else self.fonte_texto
        )

        draw.text(
            (x, y),
            texto,
            fill=(70, 50, 30, 255),
            font=fonte
        )