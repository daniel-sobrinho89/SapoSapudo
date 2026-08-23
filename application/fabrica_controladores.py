from application.usecases.aldeao.controlar_comportamento_aldeao import (
    ControlarComportamentoAldeaoUseCase,
)
from application.usecases.aldeao.cortar_arvore import CortarArvoreUseCase
from application.usecases.aldeao.obter_carne import ObterCarneUseCase
from application.usecases.aldeao.obter_ouro import ObterOuroUseCase
from application.usecases.construcao.defender_construcao import (
    DefenderConstrucaoUseCase,
)
from application.usecases.construcao.destruir_construcao import (
    DestruirConstrucaoUseCase,
)
from application.usecases.controlar_comportamento_ovelha import (
    ControlarComportamentoOvelhaUseCase,
)
from application.usecases.goblin.atacar import AtacarGoblinUseCase
from application.usecases.goblin.controlar_comportamento_goblin_tocha import (
    ControlarComportamentoGoblinTochaUseCase,
)
from application.usecases.personagem.morte_personagem import MortePersonagemUseCase
from application.usecases.sapudo.controlar_comportamento_sapudo import (
    ControlarComportamentoSapudoUseCase,
)
from application.usecases.soldado.atacar import AtacarSoldadoUseCase
from application.usecases.soldado.controlar_comportamento_soldado import (
    ControlarComportamentoSoldadoUseCase,
)
from core.game_config import obter_config

USECASES = {
    "ControlarComportamentoSapudoUseCase": lambda c: ControlarComportamentoSapudoUseCase(
        c.navegacao, c.mover_personagem
    ),
    "ControlarComportamentoAldeaoUseCase": lambda c: ControlarComportamentoAldeaoUseCase(
        c.navegacao, c.mover_personagem
    ),
    "ControlarComportamentoSoldadoUseCase": lambda c: ControlarComportamentoSoldadoUseCase(
        c.navegacao, c.mover_personagem
    ),
    "ControlarComportamentoGoblinTochaUseCase": lambda c: ControlarComportamentoGoblinTochaUseCase(
        c.navegacao, c.mover_personagem
    ),
    "ControlarComportamentoOvelhaUseCase": lambda c: ControlarComportamentoOvelhaUseCase(
        c.navegacao, c.mover_personagem
    ),
    "MortePersonagemUseCase": lambda c: MortePersonagemUseCase(c),
    "CortarArvoreUseCase": lambda c: CortarArvoreUseCase(c),
    "ObterOuroUseCase": lambda c: ObterOuroUseCase(c),
    "ObterCarneUseCase": lambda c: ObterCarneUseCase(c),
    "AtacarSoldadoUseCase": lambda c: AtacarSoldadoUseCase(c),
    "AtacarGoblinUseCase": lambda c: AtacarGoblinUseCase(c),
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
