from dataclasses import dataclass


@dataclass(frozen=True)
class RegiaoMapa:
    id: str
    nome: str
    tipo: str
    x: int
    y: int
    colunas: int
    linhas: int

    def contem_tile(self, coluna: int, linha: int) -> bool:
        return (
            self.x <= coluna < self.x + self.colunas
            and self.y <= linha < self.y + self.linhas
        )

    def contem_pixel(
        self,
        x: float,
        y: float,
        offset_x: float,
        offset_y: float,
        tile_size: int = 64,
    ) -> bool:
        coluna = int((x - offset_x) // tile_size)
        linha = int((y - offset_y) // tile_size)
        return self.contem_tile(coluna, linha)
