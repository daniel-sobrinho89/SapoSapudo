from application.usecases.personagem.controlar_comportamento_base import (
    ControlarComportamentoBaseUseCase,
)
from domains.personagem.maquina_estado_soldado import EstadoSoldado


class ControlarComportamentoSoldadoUseCase(ControlarComportamentoBaseUseCase):
    ESTADO = EstadoSoldado
