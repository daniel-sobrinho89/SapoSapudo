from application.usecases.urso.atacar import AtacarUrsoUseCase
from core.ciclo_dia_noite import CicloDiaNoite
from utils.config import MINUTOS_24_HORAS


def test_ciclo_24_horas_usa_config():
    assert isinstance(MINUTOS_24_HORAS, int)
    assert MINUTOS_24_HORAS == 14
    assert CicloDiaNoite.DURACAO_CICLO_SEGUNDOS == MINUTOS_24_HORAS * 60


def test_saida_do_urso_e_18_10():
    ciclo = CicloDiaNoite(hora_inicial=18 + 9 / 60)
    # Com 14 minutos por ciclo, cada hora dura 35 segundos reais e
    # cada minuto do jogo dura 35/60 segundos.
    ciclo.atualizar(35 / 60)
    assert ciclo.horario_formatado == "18:10"


def test_usecase_urso_mantem_sapudo_como_alvo():
    class FalsoSapudo:
        vida = 200

    class Cenario:
        sapudo = FalsoSapudo()
        personagens = ()

    class FalsoUrso:
        pass

    usecase = AtacarUrsoUseCase.__new__(AtacarUrsoUseCase)
    usecase.cenario_principal = Cenario()
    usecase.iniciar = lambda alvo, atacante: (
        setattr(usecase, "entidade_alvo", alvo),
        setattr(usecase, "personagem", atacante),
    )
    usecase.entidade_alvo = None
    usecase.personagem = None

    assert usecase.iniciar_ataque_noturno(FalsoUrso()) is True
    assert usecase.entidade_alvo is Cenario.sapudo
