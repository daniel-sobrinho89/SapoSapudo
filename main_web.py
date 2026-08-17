import asyncio
import logging
import platform
import sys
import time
import traceback
from contextlib import suppress

import pygame

from application.coordenador_estado_jogo import CoordenadorEstadoJogo
from domains.cenario import EstadoJogo, GerenciadorCenarios
from render.transform_utils import TransformUtils
from utils import browser_backend
from utils.config import ALTURA, LARGURA
from utils.input import init_scaling

sys.modules["utils.kivy_adapter"] = browser_backend

logging.getLogger().setLevel(logging.INFO)


def web_log(message):
    text = str(message)
    print(text, flush=True)
    if sys.platform == "emscripten":
        with suppress(Exception):
            platform.console.log(text)


def web_error(message):
    text = str(message)
    print(text, flush=True)
    if sys.platform == "emscripten":
        with suppress(Exception):
            platform.console.error(text)


pygame.display.init()
pygame.font.init()

screen = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Sapo Sapudo")
with suppress(Exception):
    if sys.platform == "emscripten":
        platform.window.canvas.style.imageRendering = "pixelated"
init_scaling(LARGURA, ALTURA, LARGURA, ALTURA)

tela = browser_backend.Surface((LARGURA, ALTURA))
transform = TransformUtils()

gerenciador_cenarios = None
cenario = None
coordenador = None
cenario_inicializado = False

web_log("SapoSapudo Web: display inicializado; aguardando início do jogo")


def pos_virtual(pos):
    # Pygame/Web canvas uses origin at the top-left, unlike Kivy/Android.
    # Reusing real_to_virtual() here would invert Y and send clicks to the
    # opposite side of the map.
    try:
        rx, ry = pos
        rw, rh = pygame.display.get_window_size()
        if rw <= 0 or rh <= 0:
            return int(rx), int(ry)
        return (
            int(rx * LARGURA / rw),
            int(ry * ALTURA / rh),
        )
    except Exception:
        return int(pos[0]), int(pos[1])


def pos_virtual_to_finger(x, y):
    # Pygame FINGER* events expose normalized top-left-origin coordinates.
    return (int(x * LARGURA), int(y * ALTURA))


def preparar_gerenciador_web():
    global gerenciador_cenarios, cenario

    if gerenciador_cenarios is None:
        gerenciador_cenarios = GerenciadorCenarios(tela, transform)
        cenario = gerenciador_cenarios.cenario_principal

    return gerenciador_cenarios


def iniciar_cenario_web():
    global coordenador, cenario_inicializado

    if cenario_inicializado:
        return True

    try:
        preparar_gerenciador_web()
        gerenciador_cenarios.estado = EstadoJogo.JOGANDO
        web_log("SapoSapudo Web: iniciando carregamento do cenário")
        cenario.carregar()
        coordenador = CoordenadorEstadoJogo(cenario)
        cenario_inicializado = True
        web_log(
            "SapoSapudo Web: entidades criadas; carregamento visual será incremental"
        )
        return True
    except Exception:
        web_error("SapoSapudo Web: erro ao iniciar o cenário")
        web_error(traceback.format_exc())
        gerenciador_cenarios.estado = EstadoJogo.ABERTURA
        return False


def processar_mouse_down(event):
    p = pos_virtual(event.pos)

    if event.button == 4:
        cenario.camera.aproximar()
        return
    if event.button == 5:
        cenario.camera.afastar()
        return

    if event.button == 1:
        if (
            not cenario_inicializado
            and gerenciador_cenarios.estado == EstadoJogo.ABERTURA
        ):
            iniciar_cenario_web()
            return

        if cenario.carregado and coordenador is not None:
            coordenador.processar_toque_down(p)


async def main():
    global coordenador, cenario_inicializado

    # Primeiro frame leve, sem carregar mapa ou sprites. No browser não
    # dependemos de double-click/touch para iniciar o jogo: isso evita que
    # diferenças de input do canvas deixem o usuário preso na abertura.
    tela.fill((20, 24, 40, 255))
    browser_backend.draw.text(
        tela,
        "Sapo Sapudo",
        (LARGURA // 2 - 90, ALTURA // 2 - 40),
        (255, 255, 255),
        32,
    )
    browser_backend.draw.text(
        tela,
        "Carregando...",
        (LARGURA // 2 - 85, ALTURA // 2 + 10),
        (210, 210, 220),
        20,
    )
    pygame.display.flip()
    await asyncio.sleep(0)

    preparar_gerenciador_web()

    iniciar_cenario_web()

    last = time.perf_counter()
    ultimo_progresso = -1
    acumulador_ia = 0.0
    passo_ia = 1.0 / 30.0

    while True:
        now = time.perf_counter()
        dt = min(now - last, 0.05)
        last = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                processar_mouse_down(event)
            elif event.type == getattr(pygame, "FINGERDOWN", -999):
                # Alguns browsers expõem toque como FINGERDOWN em vez de
                # sintetizar MOUSEBUTTONDOWN. Converta para coordenadas virtuais.
                with suppress(Exception):
                    evento_mouse = type(
                        "MouseEvent",
                        (),
                        {
                            "button": 1,
                            "pos": pos_virtual_to_finger(event.x, event.y),
                        },
                    )()
                    processar_mouse_down(evento_mouse)
            elif event.type == pygame.KEYDOWN:
                if getattr(event, "key", None) in (pygame.K_RETURN, pygame.K_SPACE):
                    iniciar_cenario_web()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and cenario.carregado and coordenador is not None:
                    coordenador.processar_toque_up(pos_virtual(event.pos))
            elif event.type == pygame.MOUSEMOTION:
                if cenario.carregado and coordenador is not None:
                    coordenador.processar_on_touch_move(pos_virtual(event.pos))
            elif (
                event.type == getattr(pygame, "FINGERUP", -998)
                and cenario.carregado
                and coordenador is not None
            ):
                p = pos_virtual_to_finger(event.x, event.y)
                coordenador.processar_toque_up(p)

        # A criação das entidades acontece uma única vez. Enquanto os assets
        # ainda estão sendo preparados, não execute IA nem renderização pesada.
        if cenario_inicializado and not cenario.carregado:
            try:
                gerenciador_cenarios.renderizar(dt)
                progresso = cenario.progresso_carregamento()
                marco = int(progresso * 100)
                if marco != ultimo_progresso and marco % 5 == 0:
                    ultimo_progresso = marco
                    web_log(f"SapoSapudo Web: carregamento {marco}%")

                # O renderizador de cenário não desenha nada pesado enquanto
                # os sprites estão incompletos. Mostramos apenas o progresso.
                browser_backend.draw.text(
                    tela,
                    f"Carregando... {int(progresso * 100)}%",
                    (LARGURA // 2 - 95, ALTURA // 2 + 50),
                    (255, 255, 255),
                    24,
                )
            except Exception:
                web_error("SapoSapudo Web: erro durante carregamento")
                web_error(traceback.format_exc())

        elif cenario_inicializado and cenario.carregado:
            # IA e navegação não precisam ser avaliadas 60 vezes por segundo.
            # Mantemos a renderização no ritmo do browser, mas executamos os
            # UseCases de comportamento em 30 Hz, reduzindo BFS, scans de
            # alvos e chamadas de colisão sem deixar o movimento perceptivelmente
            # travado.
            acumulador_ia += dt
            if acumulador_ia >= passo_ia:
                iteracoes = min(2, int(acumulador_ia / passo_ia))
                for _ in range(iteracoes):
                    coordenador.executar(passo_ia)
                    acumulador_ia -= passo_ia

            gerenciador_cenarios.atualizar(dt)
            gerenciador_cenarios.renderizar(dt)
        else:
            # fallback visual caso a inicialização falhe
            tela.fill((20, 24, 40, 255))

        target_size = pygame.display.get_window_size()
        if target_size != (LARGURA, ALTURA):
            scaled = pygame.transform.scale(tela._img, target_size)
            screen.blit(scaled, (0, 0))
        else:
            screen.blit(tela._img, (0, 0))

        pygame.display.flip()
        await asyncio.sleep(0)


asyncio.run(main())
