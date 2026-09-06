import os
from datetime import datetime

LARGURA = 1024
ALTURA = 600
FPS = 30

# Duração, em minutos reais, das 24 horas do relógio do jogo.
# Centraliza a velocidade do ciclo para facilitar manutenção.
MINUTOS_24_HORAS = 11

TITULO = "Sapo Sapudo"


# =====================================
# ÁUDIO
# =====================================

AUDIO_HABILITADO = True

MUSICA_FUNDO = "assets/musica/vila_duendes.ogg"

VOLUME_MUSICA = 0.25

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
TILE_SIZE = 64


def obter_hora_decimal():
    """Retorna a hora atual em formato decimal (ex: 14.5 para 14:30)."""
    agora = datetime.now()
    return agora.hour + (agora.minute / 60)
