from math import hypot

from core.game_config import obter_config
from utils.config import TILE_SIZE


class ChamarDefensoresUseCase:
    RAIO_DEFESA_EM_TILES = 6
    RAIO_DEFESA = RAIO_DEFESA_EM_TILES * TILE_SIZE

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal

    def executar(self, entidade_protegida, atacante, faccao):
        if entidade_protegida is None or atacante is None:
            return

        for personagem, ctrl in self.cenario_principal.controladores.items():
            if personagem is entidade_protegida:
                continue

            if personagem.vida <= 0:
                continue

            config = obter_config(personagem.nome)
            registro = self.cenario_principal.obter_entidade(personagem)
            faccao_personagem = (
                registro.get("faccao")
                if registro is not None and registro.get("faccao") is not None
                else config.get("faccao")
            )

            if config.get("grupo") == "construcoes":
                continue

            if faccao_personagem != faccao:
                continue

            if not self._esta_no_raio(entidade_protegida, personagem):
                continue

            atacar = ctrl.get("acoes", {}).get("atacar")

            if atacar is None:
                continue

            usecase = atacar.get("usecase")

            if usecase is None:
                continue

            if usecase.entidade_alvo is not None:
                continue

            usecase.iniciar(
                atacante,
                personagem,
            )

    def _esta_no_raio(self, origem, personagem):
        distancia = hypot(
            personagem.x - origem.x,
            personagem.y - origem.y,
        )

        return distancia <= self.RAIO_DEFESA
