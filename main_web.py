import asyncio
import logging
import platform
import sys
import time
import traceback
from contextlib import suppress

import pygame

from utils import browser_backend

sys.modules["utils.kivy_adapter"] = browser_backend

from application.coordenador_estado_jogo import CoordenadorEstadoJogo
from domains.cenario import EstadoJogo, GerenciadorCenarios
from render.transform_utils import TransformUtils
from utils.config import ALTURA, LARGURA
from utils.input import init_scaling

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
        platform.window.canvas.style.webkitImageRendering = "pixelated"
        platform.window.canvas.style.msInterpolationMode = "nearest-neighbor"
init_scaling(LARGURA, ALTURA, LARGURA, ALTURA)

tela = browser_backend.Surface((LARGURA, ALTURA))
transform = TransformUtils()

gerenciador_cenarios = None
cenario = None
coordenador = None
cenario_inicializado = False
carregamento_iniciado = False
preloader_ocultado = False
maior_progresso_carregamento = 0.0

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
    global cenario_inicializado, carregamento_iniciado

    if cenario_inicializado:
        return True

    try:
        preparar_gerenciador_web()
        gerenciador_cenarios.estado = EstadoJogo.JOGANDO
        cenario.iniciar_carregamento()
        carregamento_iniciado = True
        web_log("SapoSapudo Web: carregamento do cenário iniciado")
        return True
    except Exception:
        web_error("SapoSapudo Web: erro ao iniciar carregamento do cenário")
        web_error(traceback.format_exc())
        gerenciador_cenarios.estado = EstadoJogo.ABERTURA
        return False


def preparar_preloader_web():
    """Assume o controle do carregamento Pygbag assim que Python inicia."""
    if sys.platform != "emscripten":
        return

    with suppress(Exception):
        root = platform.document.documentElement
        root.classList.add("sapo-python")
        root.classList.remove("sapo-ready")
        root.style.setProperty("--sapo-percent", '"0%"')
        status = platform.document.getElementById("status")
        progress = platform.document.getElementById("progress")
        if status is not None:
            status.innerText = "Carregando o mundo..."
        if progress is not None:
            progress.max = 100
            progress.value = 0


def atualizar_preloader_web(progresso):
    """Atualiza exclusivamente a barra oficial do Pygbag, sempre para frente."""
    if sys.platform != "emscripten":
        return

    percentual = max(0, min(100, int(progresso * 100)))

    with suppress(Exception):
        root = platform.document.documentElement
        root.style.setProperty("--sapo-percent", f'"{percentual}%"')
        progress = platform.document.getElementById("progress")
        if progress is not None:
            atual = int(getattr(progress, "value", 0) or 0)
            if percentual > atual:
                progress.value = percentual


def finalizar_preloader_web():
    """Esconde a interface oficial somente depois do primeiro frame pronto."""
    global preloader_ocultado

    if preloader_ocultado or sys.platform != "emscripten":
        return

    with suppress(Exception):
        root = platform.document.documentElement
        root.classList.add("sapo-ready")
        status = platform.document.getElementById("status")
        progress = platform.document.getElementById("progress")
        if status is not None:
            status.innerText = "100%"
        if progress is not None:
            progress.value = 100
        preloader_ocultado = True


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
    global \
        coordenador, \
        cenario_inicializado, \
        carregamento_iniciado, \
        maior_progresso_carregamento, \
        preloader_ocultado

    preparar_preloader_web()
    await asyncio.sleep(0)

    preparar_gerenciador_web()

    iniciar_cenario_web()

    last = time.perf_counter()
    ultimo_progresso = -1

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

        primeiro_frame_jogo = False

        if carregamento_iniciado and not cenario.carregado:
            try:
                cenario.processar_carregamento(max_tipos=1)

                gerenciador_cenarios.renderizar(dt)
                progresso = cenario.progresso_carregamento()
                progresso = max(progresso, maior_progresso_carregamento)
                maior_progresso_carregamento = progresso
                if not cenario.carregado:
                    progresso = min(progresso, 0.99)
                marco = int(progresso * 100)
                if marco != ultimo_progresso and marco % 5 == 0:
                    ultimo_progresso = marco
                    web_log(f"SapoSapudo Web: carregamento {marco}%")

                atualizar_preloader_web(progresso)
            except Exception:
                web_error("SapoSapudo Web: erro durante carregamento")
                web_error(traceback.format_exc())

        elif carregamento_iniciado and cenario.carregado:
            if not cenario_inicializado:
                coordenador = CoordenadorEstadoJogo(cenario)
                cenario_inicializado = True
                web_log("SapoSapudo Web: cenário carregado; preparando primeiro frame")

            coordenador.executar(dt)
            gerenciador_cenarios.atualizar(dt)
            gerenciador_cenarios.renderizar(dt)
            primeiro_frame_jogo = bool(
                getattr(cenario, "primeiro_frame_renderizado", False)
            )
            if primeiro_frame_jogo and not preloader_ocultado:
                finalizar_preloader_web()
                web_log("SapoSapudo Web: primeiro frame pronto; iniciando jogo")
        else:
            # fallback visual caso a inicialização falhe
            tela.fill((20, 24, 40, 255))

        screen.fill((24, 56, 74))
        screen.blit(tela._img, (0, 0))

        pygame.display.flip()

        await asyncio.sleep(0)


asyncio.run(main())
