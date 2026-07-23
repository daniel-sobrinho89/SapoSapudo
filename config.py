import os

LARGURA = 1024
ALTURA = 600
FPS = 30

TITULO = "Sapo Sapudo"


# =====================================
# ÁUDIO
# =====================================

AUDIO_HABILITADO = False

MUSICA_FUNDO = "assets/musica/vila_duendes.ogg"

VOLUME_MUSICA = 0.25


# =====================================
# POEIRA
# =====================================

QUANTIDADE_POEIRA = 8

# =====================================
# constantes
# =====================================

ESCALA_BASE = 0.13
ESCALA_PERSONAGEM = 2.8

ESCALA = ESCALA_BASE * ESCALA_PERSONAGEM

CENTRO_OFFSET_Y = 170
CHAO_Y = 520

CENTRO_Y = ALTURA // 2 + CENTRO_OFFSET_Y

IS_ANDROID = "ANDROID_ARGUMENT" in os.environ
