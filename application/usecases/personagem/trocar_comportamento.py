from domains.personagem.maquina_estado import EstadoAldeao  # noqa: F401
from domains.personagem.maquina_estado_goblin_tocha import (
    EstadoGoblinTocha,  # noqa: F401
)
from domains.personagem.maquina_estado_sapudo import EstadoSapudo  # noqa: F401
from domains.personagem.maquina_estado_soldado import EstadoSoldado  # noqa: F401


class TrocarComportamentoUseCase:
    def executar(
        self,
        controlador,
        personagem,
        navegacao,
        destino_x,
        destino_y,
    ):
        for acao in controlador["acoes"].values():
            acao["usecase"].cancelar()

        atacar = controlador["acoes"].get("atacar")
        if atacar is not None:
            bloquear = getattr(
                atacar["usecase"],
                "bloquear_busca_automatica_ate_destino",
                None,
            )
            if bloquear is not None:
                bloquear()

        if not navegacao.pode_andar(destino_x, destino_y, personagem.altura):
            rota = navegacao.calcular_rota(
                personagem.x,
                personagem.y,
                destino_x,
                destino_y,
                personagem.altura,
            )
            if not rota:
                personagem.destino_x = personagem.x
                personagem.destino_y = personagem.y
                controlador["padrao"].parar(personagem)
                return False

        controlador["padrao"].iniciar(
            personagem,
            destino_x,
            destino_y,
        )

        # Uma ordem manual redefine a área de movimentação autônoma.
        personagem.definir_base_movimento(destino_x, destino_y)

        return True
