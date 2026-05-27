import pygame

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

character_renderer = CharacterRenderer(
    tela,
    assets,
    transform
)

respiracao = Respiracao()

animacoes_faciais = AnimacoesFaciais()

animacao_folha = AnimacaoFolha()

ambiente = Ambiente()

particulas = [

    ParticulaPoeira(
        LARGURA,
        ALTURA
    )

    for _ in range(14)
]

frasco_climatico = FrascoClimatico()

# =========================================
# POSITION
# =========================================

centro_x = LARGURA // 2

centro_y = (
    ALTURA // 2
    + CENTRO_OFFSET_Y
)

# =========================================
# LOOP
# =========================================

rodando = True

while rodando:

    dt = clock.tick(FPS) / 1000.0

    # UPDATE

    ambiente.atualizar(dt)

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:

            rodando = False

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

    for particula in particulas:

        particula.atualizar(
            ambiente
        )

    # =====================================
    # RENDER
    # =====================================

    background_renderer.desenhar()

    # FRASCO (ancorar verticalmente ao personagem)
    frasco_climatico.renderizar(tela, centro_y)

    # PARTÍCULAS
    for particula in particulas:

        particula.desenhar(tela)

    # PERSONAGEM
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

    pygame.display.flip()

pygame.quit()