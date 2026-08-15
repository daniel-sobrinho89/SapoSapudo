from application.usecases.personagem.controlar_comportamento_base import (
    ControlarComportamentoBaseUseCase,
)
from domains.personagem.maquina_estado_goblin_tocha import EstadoGoblinTocha


class ControlarComportamentoGoblinTochaUseCase(ControlarComportamentoBaseUseCase):
    ESTADO = EstadoGoblinTocha
