from application.usecases.personagem.controlar_comportamento_base import (
    ControlarComportamentoBaseUseCase,
)
from domains.personagem.maquina_estado import EstadoAldeao


class ControlarComportamentoAldeaoUseCase(ControlarComportamentoBaseUseCase):
    ESTADO = EstadoAldeao
