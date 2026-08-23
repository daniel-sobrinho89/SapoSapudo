import json
from pathlib import Path

from utils.config import TILE_SIZE


class HeadlessTileMap:
    """TileMap mínimo, determinístico e compatível com NavegacaoMapa."""

    def __init__(self, data):
        self.largura = data["colunas"]
        self.altura = data["linhas"]
        self.bloqueados = {tuple(p) for p in data.get("bloqueados", [])}
        self.alturas = {
            tuple(map(int, k.split(","))): int(v)
            for k, v in data.get("alturas", {}).items()
        }
        self.degraus = {
            tuple(map(int, k.split(","))): v for k, v in data.get("degraus", {}).items()
        }

    @classmethod
    def from_file(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _coordenada_valida(self, coluna, linha):
        return 0 <= coluna < self.largura and 0 <= linha < self.altura

    def tile_para_pixel(self, coluna, linha):
        return coluna * TILE_SIZE, linha * TILE_SIZE

    def pixel_para_tile(self, x, y):
        return int(x // TILE_SIZE), int(y // TILE_SIZE)

    def obter_altura(self, coluna, linha):
        return self.alturas.get((coluna, linha), 0)

    def obter_degrau(self, coluna, linha):
        return self.degraus.get((coluna, linha))

    def eh_degrau(self, coluna, linha):
        return (coluna, linha) in self.degraus

    def obter_transicao_degrau(self, c0, l0, c1, l1, altura):
        degrau = self.degraus.get((c1, l1))
        if not degrau:
            return None
        if altura in (degrau["altura_baixa"], degrau["altura_alta"]):
            return (
                degrau["altura_alta"]
                if altura == degrau["altura_baixa"]
                else degrau["altura_baixa"]
            )
        return None

    def pode_andar(self, coluna, linha, altura):
        if not self._coordenada_valida(coluna, linha):
            return False
        if (coluna, linha) in self.bloqueados:
            return False
        altura_tile = self.obter_altura(coluna, linha)
        if (coluna, linha) in self.degraus:
            degrau = self.degraus[(coluna, linha)]
            return altura in (degrau["altura_baixa"], degrau["altura_alta"])
        return altura == altura_tile

    def pode_andar_pixel(self, x, y, altura, margem_borda=0):
        c, lin = self.pixel_para_tile(x, y)
        return self.pode_andar(c, lin, altura)


def carregar(path):
    return HeadlessTileMap.from_file(path)
