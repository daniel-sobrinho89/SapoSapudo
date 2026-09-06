from application.usecases.aldeao.cortar_arvore import CortarArvoreUseCase
from application.usecases.aldeao.obter_carne import ObterCarneUseCase
from application.usecases.aldeao.obter_ouro import ObterOuroUseCase
from application.usecases.bandido.atacar import AtacarBandidoUseCase
from application.usecases.cobra.atacar import AtacarCobraUseCase
from application.usecases.construcao.defender_construcao import (
    DefenderConstrucaoUseCase,
)
from application.usecases.construcao.destruir_construcao import (
    DestruirConstrucaoUseCase,
)
from application.usecases.controlar_comportamento_ovelha import (
    ControlarComportamentoOvelhaUseCase,
)
from application.usecases.esqueleto.atacar import AtacarEsqueletoUseCase
from application.usecases.personagem.atacar import AtacarPersonagemUseCase
from application.usecases.personagem.comportamento import ControlarComportamentoUseCase
from application.usecases.personagem.morte_personagem import MortePersonagemUseCase
from application.usecases.soldado.atacar import AtacarSoldadoUseCase
from application.usecases.urso.atacar import AtacarUrsoUseCase
from core.game_config import obter_config

USECASES = {
    # Comportamento genérico parametrizado pelo estado de cada personagem.
    "ControlarComportamentoAldeaoUseCase": lambda c: ControlarComportamentoUseCase(
        c.navegacao, mover=c.mover_personagem, world_context=c.world_context
    ),
    "ControlarComportamentoSoldadoUseCase": lambda c: ControlarComportamentoUseCase(
        c.navegacao, mover=c.mover_personagem, world_context=c.world_context
    ),
    "ControlarComportamentoGoblinTochaUseCase": lambda c: ControlarComportamentoUseCase(
        c.navegacao, mover=c.mover_personagem, world_context=c.world_context
    ),
    "ControlarComportamentoEsqueletoUseCase": lambda c: ControlarComportamentoUseCase(
        c.navegacao, mover=c.mover_personagem, world_context=c.world_context
    ),
    "ControlarComportamentoOvelhaUseCase": lambda c: ControlarComportamentoOvelhaUseCase(
        c.navegacao, c.mover_personagem, c.world_context
    ),
    "MortePersonagemUseCase": lambda c: MortePersonagemUseCase(c),
    "CortarArvoreUseCase": lambda c: CortarArvoreUseCase(c),
    "ObterOuroUseCase": lambda c: ObterOuroUseCase(c),
    "ObterCarneUseCase": lambda c: ObterCarneUseCase(c),
    "AtacarSoldadoUseCase": lambda c: AtacarSoldadoUseCase(c),
    "AtacarPersonagemUseCase": lambda c: AtacarPersonagemUseCase(c),
    "AtacarEsqueletoUseCase": lambda c: AtacarEsqueletoUseCase(c),
    "AtacarCobraUseCase": lambda c: AtacarCobraUseCase(c),
    "AtacarBandidoUseCase": lambda c: AtacarBandidoUseCase(c),
    "AtacarUrsoUseCase": lambda c: AtacarUrsoUseCase(c),
    "DefenderConstrucaoUseCase": lambda c: DefenderConstrucaoUseCase(c),
    "DestruirConstrucaoUseCase": lambda c: DestruirConstrucaoUseCase(c),
}


class FabricaControladores:
    @staticmethod
    def criar(entidade, cenario):
        config = obter_config(entidade.nome)

        ia = config.get("ia")
        if ia is None:
            return None

        controlador = {
            "padrao": USECASES[ia["padrao"]](cenario),
            "morte": USECASES[ia["morte"]](cenario),
            "acoes": {},
        }

        for nome_acao, cfg in ia["acoes"].items():
            alvos = cfg["alvos"]

            if isinstance(alvos, str):
                itens = getattr(cenario, alvos)
            else:
                itens = [getattr(cenario, nome) for nome in alvos]

            controlador["acoes"][nome_acao] = {
                "itens": itens,
                "usecase": USECASES[cfg["usecase"]](cenario),
            }

        return controlador
