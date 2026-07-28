import json

from utils.paths import BASE_DIR

with open(BASE_DIR / "data/sprites_config.json", encoding="utf8") as f:
    CONFIG = json.load(f)


def obter_config(nome):
    return CONFIG[nome.lower()]


def obter_tipos():
    return CONFIG.keys()
