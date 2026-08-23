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

from application.cenario import EstadoJogo, GerenciadorCenarios
from application.coordenador_estado_jogo import CoordenadorEstadoJogo
from render.transform_utils import TransformUtils
from utils.config import ALTURA, FPS, LARGURA
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

# Browsers mobile podem emitir FINGER* e também o MOUSE* sintético para o
# mesmo toque. Sem deduplicação, um único toque chega duas vezes ao jogo e
# o detector de duplo clique interpreta o par como uma ação distinta.
_ULTIMO_EVENTO_TOQUE_WEB = None
_ULTIMO_EVENTO_MOUSE_WEB = None
_JANELA_DUPLICATA_TOQUE = 0.35
_DISTANCIA_DUPLICATA_TOQUE = 28.0


def _web_eh_dispositivo_tactil():
    if sys.platform != "emscripten":
        return False
    with suppress(Exception):
        return int(getattr(platform.window.navigator, "maxTouchPoints", 0) or 0) > 0
    return False


_WEB_TOUCH_DEVICE = _web_eh_dispositivo_tactil()


def _evento_web_duplicado(origem, pos):
    global _ULTIMO_EVENTO_TOQUE_WEB, _ULTIMO_EVENTO_MOUSE_WEB

    agora = time.monotonic()
    pos = (float(pos[0]), float(pos[1]))

    anterior = (
        _ULTIMO_EVENTO_MOUSE_WEB if origem == "touch" else _ULTIMO_EVENTO_TOQUE_WEB
    )

    if anterior is not None:
        instante, x, y = anterior
        if (
            agora - instante <= _JANELA_DUPLICATA_TOQUE
            and (pos[0] - x) ** 2 + (pos[1] - y) ** 2 <= _DISTANCIA_DUPLICATA_TOQUE**2
        ):
            return True

    registro = (agora, pos[0], pos[1])
    if origem == "touch":
        _ULTIMO_EVENTO_TOQUE_WEB = registro
    else:
        _ULTIMO_EVENTO_MOUSE_WEB = registro
    return False


web_log("SapoSapudo Web: display inicializado; aguardando início do jogo")


def pos_virtual(pos):
    # Pygame/Web e HUD usam origem no topo; apenas convertemos a escala
    # do canvas real para a resolução virtual fixa.
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


def processar_mouse_down(event, origem="mouse"):
    p = pos_virtual(event.pos)

    if event.button == 1 and _evento_web_duplicado(origem, p):
        return

    if event.button == 4:
        cenario.camera.aproximar(p)
        return
    if event.button == 5:
        cenario.camera.afastar(p)
        return

    if event.button == 1:
        if (
            not cenario_inicializado
            and gerenciador_cenarios.estado == EstadoJogo.ABERTURA
        ):
            iniciar_cenario_web()
            return

        if cenario.carregado and coordenador is not None:
            # O detector de duplo clique continua ativo no touch.
            # A deduplicacao acima remove apenas o MOUSEBUTTONDOWN sintetico
            # correspondente ao mesmo toque. Assim:
            #   1 toque real -> 1 selecao
            #   2 toques reais -> duplo clique/menu
            coordenador.processar_toque_down(p, permitir_duplo_clique=True)


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
        frame_start = time.perf_counter()
        now = frame_start
        dt = min(now - last, 0.05)
        last = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                processar_mouse_down(event)
            elif event.type == getattr(pygame, "FINGERDOWN", -999):
                # Em mobile, trate o FINGERDOWN como o evento primário.
                # Não sintetize um MOUSEBUTTONDOWN, pois alguns browsers já
                # produzem esse evento automaticamente para o mesmo toque.
                p = pos_virtual_to_finger(event.x, event.y)
                if not _evento_web_duplicado("touch", p):
                    if (
                        not cenario_inicializado
                        and gerenciador_cenarios.estado == EstadoJogo.ABERTURA
                    ):
                        iniciar_cenario_web()
                    elif cenario.carregado and coordenador is not None:
                        # FINGERDOWN e a entrada primaria no touch.
                        # O detector deve permanecer ativo para reconhecer
                        # dois toques reais como duplo clique; o MOUSE*
                        # sintetico do browser e descartado pela deduplicacao.
                        coordenador.processar_toque_down(p, permitir_duplo_clique=True)
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

        # O jogo foi projetado para 30 FPS. Sem pacing, o loop assíncrono do
        # browser roda tão rápido quanto o dispositivo permitir e disputa CPU
        # com o próprio navegador, especialmente em celulares. Limitamos o
        # ritmo ao FPS-alvo sem reduzir resolução, sprites ou qualidade.
        restante = (1.0 / FPS) - (time.perf_counter() - frame_start)
        await asyncio.sleep(max(0.0, restante))


asyncio.run(main())
