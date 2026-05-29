# =========================================
# MAIN.PY
# =========================================

import pygame
import threading

from config import *
from constants import *

from systems.respiracao import Respiracao
from systems.animacoes_faciais import AnimacoesFaciais
from systems.animacao_folha import AnimacaoFolha
from systems.ambiente import Ambiente
from systems.particulas.poeira import ParticulaPoeira
from systems.clima.frasco import FrascoClimatico

from render.asset_manager import AssetManager
from render.transform_utils import TransformUtils
from render.background_renderer import BackgroundRenderer
from render.character_renderer import CharacterRenderer

from systems.clima.clima_service import ClimaService
from systems.clima.sistema_nuvens import SistemaNuvens

from render.duende_renderer import DuendeRenderer
from entities.duende_neblina import DuendeNeblina
from systems.audio_manager import AudioManager

# =========================================
# INIT
# =========================================

pygame.init()

# =========================================
# WINDOW
# =========================================

tela = pygame.display.set_mode(
    (LARGURA, ALTURA)
)

pygame.display.set_caption(
    TITULO
)

clock = pygame.time.Clock()

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

character_renderer = CharacterRenderer(
    tela,
    assets,
    transform
)

respiracao = Respiracao()
animacoes_faciais = AnimacoesFaciais()
animacao_folha = AnimacaoFolha()

duende = DuendeNeblina()

renderer_duende = DuendeRenderer(
    tela,
    assets
)

# =========================================
# FRASCO
# =========================================

frasco_climatico = FrascoClimatico()

particulas = [
    ParticulaPoeira(
        frasco_climatico.area_particulas
    )
    for _ in range(14)
]

# =========================================
# CLIMA
# =========================================

clima_service = ClimaService()

sistema_nuvens = SistemaNuvens(
    frasco_climatico.area_interna
)

# =========================================
# POSITION
# =========================================

centro_x = LARGURA // 2

centro_y = (
    ALTURA // 2
    + CENTRO_OFFSET_Y
)

# =========================================
#   AUDIO
# =========================================

audio = AudioManager()

audio.tocar_musica(
    "assets/musica/vila_duendes.mp3",
    volume=0.25
)

# =========================================
# LOOP
# =========================================

rodando = True

clima_atualizando = False

while rodando:

    dt = min(
        clock.tick(FPS) / 1000.0,
        0.05
    )

    # =====================================
    # EVENTOS
    # =====================================

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:

            rodando = False

    # =====================================
    # CLIMA
    # =====================================

    if (
        clima_service.precisa_atualizar()
        and not clima_atualizando
    ):

        clima_atualizando = True

        def atualizar_clima():

            global clima_atualizando

            try:
                clima_service.atualizar()
            finally:
                clima_atualizando = False

        threading.Thread(
            target=atualizar_clima,
            daemon=True
        ).start()

    clima_service.atualizar_visual(dt)

    # =====================================
    # UPDATE
    # =====================================

    ambiente.atualizar(dt)

    frasco_climatico.atualizar_posicao(centro_y)

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

    respiracao.atualizar(
        dt,
        animacoes_faciais.dormindo
    )

    animacoes_faciais.atualizar(dt)

    animacao_folha.atualizar(
        dt,
        respiracao.intensidade,
        ambiente
    )

    # =====================================
    # PONTOS DE INTERESSE
    # =====================================

    sapo_x = centro_x
    sapo_y = centro_y

    pote_x = centro_x - 260
    pote_y = centro_y + 40

    # =====================================
    # DUENDE
    # =====================================

    duende.atualizar(
        dt,
        sapo_x,
        sapo_y,
        pote_x,
        pote_y,
        clima_service,
        frasco_climatico.area_interna
    )

    # =====================================
    # PARTÍCULAS
    # =====================================

    for particula in particulas:

        particula.atualizar(
            ambiente
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
    character_renderer.renderizar(
        centro_x,
        centro_y,
        ESCALA,
        ESCALA_PERSONAGEM,
        respiracao,
        animacoes_faciais,
        animacao_folha,
        ambiente
    )

    # DUENDE
    renderer_duende.renderizar(duende)

    pygame.display.flip()

pygame.quit()