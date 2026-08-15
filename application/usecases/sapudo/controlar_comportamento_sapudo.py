from application.usecases.personagem.controlar_comportamento_base import (
    ControlarComportamentoBaseUseCase,
)
from domains.personagem.maquina_estado_sapudo import EstadoSapudo


class ControlarComportamentoSapudoUseCase(ControlarComportamentoBaseUseCase):
    ESTADO = EstadoSapudo
