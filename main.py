# =========================================
# MAIN.PY
# =========================================

import pygame
import threading
import os
import math

from config import *
from constants import *

from entities.sapo import Sapo
from systems.animacoes_folha import AnimacoesFolha
from systems.ambiente import Ambiente
from systems.particulas.poeira import ParticulaPoeira
from systems.clima.frasco import FrascoClimatico

from render.asset_manager import AssetManager
from render.transform_utils import TransformUtils
from render.background_renderer import BackgroundRenderer
from render.sapo_renderer import SapoRenderer

from systems.clima.clima_service import ClimaService
from systems.clima.sistema_nuvens import SistemaNuvens

from render.duende_renderer import DuendeRenderer
from entities.duende_neblina import DuendeNeblina
from systems.audio_manager import AudioManager
from entities.violao import Violao
from render.violao_renderer import ViolaoRenderer
from entities.semente import Semente
from render.semente_renderer import SementeRenderer

# =========================================
# INIT
# =========================================

pygame.init()

# =========================================
# WINDOW
# =========================================

# detectar resolução física do dispositivo
info = pygame.display.Info()
LARGURA_REAL = info.current_w
ALTURA_REAL = info.current_h

# criar janela na resolução real
screen = pygame.display.set_mode(
    (LARGURA_REAL, ALTURA_REAL)
)

pygame.display.set_caption(
    TITULO
)

# superficie virtual usada por todo o jogo (resolução lógica fixa)
tela_virtual = pygame.Surface((LARGURA, ALTURA))

# manter a variável `tela` como a superfície virtual para compatibilidade
tela = tela_virtual

clock = pygame.time.Clock()

from utils.input import (
    init_scaling,
    event_pos_virtual,
    obter_posicao_ponteiro,
    virtual_to_real
)

# inicializar escala para helpers de input
init_scaling(LARGURA_REAL, ALTURA_REAL, LARGURA, ALTURA)

# detectar se estamos rodando no Android (Buildozer)
IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ


# =========================================
# POSITION
# =========================================

centro_x = LARGURA // 2

centro_y = (
    ALTURA // 2
    + CENTRO_OFFSET_Y
)

# =========================================
# SYSTEMS
# =========================================

assets = AssetManager()

transform = TransformUtils()

background_renderer = BackgroundRenderer(
    tela,
    LARGURA,
    ALTURA
)


ambiente = Ambiente()

sapo_renderer = SapoRenderer(
    tela,
    assets,
    transform
)

animacoes_folha = AnimacoesFolha()

duende = DuendeNeblina()

renderer_duende = DuendeRenderer(
    tela,
    assets
)

violao = Violao()

renderer_violao = ViolaoRenderer(
    tela,
    assets
)

duende.violao_monitorado = violao

semente = Semente()

renderer_semente = SementeRenderer(
    tela,
    assets
)

# =========================================
# FRASCO
# =========================================

frasco_climatico = FrascoClimatico()

frasco_climatico.atualizar_posicao(centro_y)

particulas = [
    ParticulaPoeira(
        frasco_climatico.area_particulas,
        frasco_climatico.area_pote
    )
    for _ in range(QUANTIDADE_POEIRA)
]

# associar área protegida (pote) para que partículas dentro do pote não sofram vento
for p in particulas:
    p.area_protegida = frasco_climatico.area_pote

    p.protegido = (
        p.area_protegida.collidepoint(
            int(p.x),
            int(p.y)
        )
    )

# =========================================
# CLIMA
# =========================================

clima_service = ClimaService()

sistema_nuvens = SistemaNuvens(
    frasco_climatico.area_interna
)


# ENTIDADE SAPO
sapo = Sapo(centro_x, centro_y)

# =========================================
#   AUDIO
# =========================================

audio = AudioManager()

audio.iniciar()

# =========================================
# LOOP
# =========================================

rodando = True

drag_duende = False

drag_violao = False

while rodando:

    dt = min(
        clock.tick(FPS) / 1000.0,
        0.05
    )

    # =====================================
    # EVENTOS
    # =====================================

    for evento in pygame.event.get():

        # converter posição do evento (resolução real -> virtual)
        pos_virtual = event_pos_virtual(evento)

        # mapear eventos de toque (Android) para tipos compatíveis com mouse
        mtype = evento.type
        mbutton = getattr(evento, 'button', None)

        if getattr(pygame, 'FINGERDOWN', None) is not None and evento.type == pygame.FINGERDOWN:
            mtype = pygame.MOUSEBUTTONDOWN
            mbutton = 1

        if getattr(pygame, 'FINGERMOTION', None) is not None and evento.type == pygame.FINGERMOTION:
            mtype = pygame.MOUSEMOTION

        if getattr(pygame, 'FINGERUP', None) is not None and evento.type == pygame.FINGERUP:
            mtype = pygame.MOUSEBUTTONUP
            mbutton = 1

        if evento.type == pygame.QUIT:

            rodando = False

        # Android back button should quit (only on Android)
        if IS_ANDROID and evento.type == pygame.KEYDOWN:
            back_keys = [pygame.K_ESCAPE, getattr(pygame, 'K_AC_BACK', None)]
            if evento.key in back_keys:
                rodando = False

        # =====================================
        # MOUSE DOWN
        # =====================================

        if (
            mtype == pygame.MOUSEBUTTONDOWN
            and mbutton == 1
        ):

            if duende.cabeca_rect.collidepoint(
                pos_virtual
            ):
                drag_duende = True

                duende.iniciar_arraste(
                    *pos_virtual
                )


            elif renderer_violao.obter_rect(violao).collidepoint(
                pos_virtual
            ):

                drag_violao = True

                violao.iniciar_arraste(
                    *pos_virtual
                )

            if (
                violao.acoplado
                and sapo_renderer.corpo_rect.collidepoint(
                    pos_virtual
                )
            ):
                violao.acoplado = False

                sapo.parar_violao()

                drag_violao = True

                audio.alternar()
                

                violao.iniciar_arraste(
                    *pos_virtual
                )

        # =====================================
        # DRAG
        # =====================================

        if mtype == pygame.MOUSEMOTION:

            if drag_violao:

                violao.mover_arraste(
                    *pos_virtual
                )

            if drag_duende:

                duende.mover_arraste(
                    *pos_virtual
                )

        # =====================================
        # SOLTOU
        # =====================================

        if (
            mtype == pygame.MOUSEBUTTONUP
            and mbutton == 1
        ):

            if drag_violao:

                drag_violao = False

                violao.finalizar_arraste()

                area_sapo = pygame.Rect(
                    centro_x - 80,
                    centro_y - 80,
                    160,
                    160
                )

                if (
                    area_sapo.collidepoint(
                        violao.x,
                        violao.y
                    )
                    and sapo.pode_receber_violao()
                ):

                    violao.acoplado = True

                    sapo.iniciar_violao()

                    violao.x = centro_x + 5
                    violao.y = centro_y + 20

                else:

                    violao.iniciar_queda()

                    if duende.pode_resgatar_violao():

                        # só teleportar se realmente estiver longe o suficiente
                        distancia_violao = abs(violao.x - duende.x)
                        MIN_TELEPORT_DIST = 120

                        if not duende.consegue_alcancar_antes_da_queda(
                            violao
                        ) and distancia_violao > MIN_TELEPORT_DIST:
                            duende.teleportar_para_violao(
                                violao
                            )

                        duende.iniciar_resgate_violao(
                            violao
                        )

            if drag_duende:

                drag_duende = False

                duende.finalizar_arraste(frasco_climatico.area_interna)

                if duende.esta_dentro_do_frasco(
                    frasco_climatico.area_interna
                ):

                    duende.animacoes.iniciar_sono()

                    duende.animacoes.iniciar_sono_programado()

                elif duende.animacoes.dormindo:

                    duende.animacoes.iniciar_acordar()

                    duende.animacoes.cancelar_sono_programado()

                    duende.escolher_novo_destino()

    # =====================================
    # CLIMA
    # =====================================

    if clima_service.precisa_atualizar():

        def atualizar_clima():

            clima_service.atualizar()

        threading.Thread(
            target=atualizar_clima,
            daemon=True
        ).start()

    clima_service.atualizar_visual(dt)

    # pequena contribuição do vento climático para o ambiente local (com sinal de direção)
    direcao_rad = math.radians(clima_service.wind_direction + 180)
    sinal_direcao = math.sin(direcao_rad)

    influencia_clima = (
        sinal_direcao
        * clima_service.wind_speed
        * 0.15
    )

    if getattr(
        clima_service,
        'rajada_ativa',
        False
    ):
        influencia_clima += (
            sinal_direcao
            * clima_service.wind_speed
            * 0.35
        )

    # aumentar sensibilidade da folha durante rajada para que ela respeite a rajada_vento
    if getattr(clima_service, 'rajada_ativa', False):
        animacoes_folha.intensidade_vento = 5.0
    else:
        animacoes_folha.intensidade_vento = 1.8

    # =====================================
    # UPDATE
    # =====================================

    # As partículas mantêm a referência a `area_pote` (retângulo do frasco)
    # O retângulo é atualizado em `frasco_climatico.atualizar_posicao`,
    # então não precisamos resetar as partículas a cada frame.

    ambiente.atualizar(dt, influencia_clima)

    # aplicar vento ao violão quando estiver caindo (usa clima_service.wind_speed, sem rajada extra)
    from systems.fisica import sistema_fisica
    if violao.caindo:
        sistema_fisica.aplicar_forca_vento(violao, clima_service, dt, sensibilidade=0.6)

    violao.atualizar(dt)

    sistema_nuvens.atualizar_area_interna(
        frasco_climatico.area_interna
    )

    sistema_nuvens.atualizar(
        dt,
        clima_service.cloudiness_visual,
        clima_service.future_cloudiness_1h,
        clima_service.future_cloudiness_2h,
        clima_service.future_cloudiness_3h,
        clima_service.wind_direction,
        clima_service.wind_speed
    )

    events = sapo.atualizar(
        dt,
        ambiente,
        animacoes_folha,
        violao
    )

    # eventos retornados por `Sapo.atualizar` que encapsulam flags internas
    if events.get("start_audio"):
        audio.alternar()

    if events.get("stop_audio"):
        audio.alternar()

    # Aplicar vento climático diretamente às entidades principais
    from systems.fisica import sistema_fisica

    # semente já recebe clima_service dentro de sua atualização
    sistema_fisica.aplicar_forca_vento(sapo, clima_service, dt, sensibilidade=0.25)


    # =====================================
    # PONTOS DE INTERESSE
    # =====================================

    sapo_x = sapo.x
    sapo_y = sapo.y

    pote_x = centro_x - 260
    pote_y = centro_y + 40

    # =====================================
    # DUENDE
    # =====================================

    duende.atualizar(
        dt,
        sapo,
        pote_x,
        pote_y,
        clima_service,
        frasco_climatico.area_interna,
        ambiente
    )

    sistema_fisica.aplicar_forca_vento(duende, clima_service, dt, sensibilidade=0.5)

    # =====================================
    # SEMENTE
    # =====================================

    semente.atualizar(
        dt,
        clima_service
    )

    # =====================================
    # PARTÍCULAS
    # =====================================

    for particula in particulas:

        particula.atualizar(
            ambiente,
            dt
        )

    # =====================================
    # RENDER
    # =====================================

    background_renderer.desenhar()

    # NUVENS NO CÉU
    sistema_nuvens.renderizar(
        tela,
        background_renderer.eh_dia()
    )

    # FRASCO
    frasco_climatico.renderizar(
        tela,
        centro_y
    )

    # PARTÍCULAS
    for particula in particulas:

        particula.desenhar(tela)

    # SAPO
    sapo_renderer.renderizar(
        sapo.x,
        sapo.y,
        ESCALA,
        sapo.animacoes
    )

    # DUENDE
    renderer_duende.renderizar(duende)

    # SEMENTE
    renderer_semente.renderizar(
        semente
    )

    # VIOLÃO
    if not violao.acoplado:

        renderer_violao.renderizar(
            violao
        )

    # escalonar a superfície virtual para a resolução real e apresentar
    scaled = pygame.transform.scale(tela, (LARGURA_REAL, ALTURA_REAL))
    screen.blit(scaled, (0, 0))
    pygame.display.flip()

pygame.quit()