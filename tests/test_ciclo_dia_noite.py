from core.ciclo_dia_noite import CicloDiaNoite


def test_periodos_e_luz():
    ciclo = CicloDiaNoite(hora_inicial=7)
    assert ciclo.periodo == "manha"
    assert ciclo.nivel_luz == CicloDiaNoite.FATOR_LUZ_MANHA

    ciclo.definir_hora(13)
    assert ciclo.periodo == "tarde"
    assert ciclo.nivel_luz == CicloDiaNoite.FATOR_LUZ_TARDE

    ciclo.definir_hora(21)
    assert ciclo.periodo == "noite"
    assert ciclo.nivel_luz == CicloDiaNoite.FATOR_LUZ_NOITE


def test_relogio_avanca_independente_do_fps():
    ciclo = CicloDiaNoite(hora_inicial=8, segundos_por_hora=60)
    ciclo.atualizar(30)
    assert ciclo.hora == 8.5
    assert ciclo.horario_formatado == "08:30"


def test_relogio_fecha_o_dia():
    ciclo = CicloDiaNoite(hora_inicial=23.5, segundos_por_hora=60)
    ciclo.atualizar(60)
    assert ciclo.hora == 0.5


def test_ciclo_padrao_dura_14_minutos():
    ciclo = CicloDiaNoite(hora_inicial=0)
    ciclo.atualizar(CicloDiaNoite.DURACAO_CICLO_SEGUNDOS)
    assert ciclo.hora == 0.0
    assert CicloDiaNoite.SEGUNDOS_POR_HORA == 35.0


def test_relogio_aceita_multiplicador_de_velocidade():
    ciclo = CicloDiaNoite(hora_inicial=18, segundos_por_hora=60)
    ciclo.atualizar(1, multiplicador=60)
    assert ciclo.hora == 19.0
