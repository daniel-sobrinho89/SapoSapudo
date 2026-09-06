from types import SimpleNamespace

from application.usecases.conversa.controlar_conversa import ControlarConversaUseCase


def _uc(hora):
    cenario = SimpleNamespace(ciclo_dia_noite=SimpleNamespace(hora=hora))
    uc = ControlarConversaUseCase.__new__(ControlarConversaUseCase)
    uc.cenario = cenario
    return uc


def test_entrada_casa_disponivel_a_partir_das_18():
    assert _uc(18.0)._casa_bernardo_disponivel_para_entrada()
    assert _uc(23.9)._casa_bernardo_disponivel_para_entrada()


def test_entrada_casa_continua_disponivel_apos_meia_noite():
    assert _uc(0.0)._casa_bernardo_disponivel_para_entrada()
    assert _uc(4.99)._casa_bernardo_disponivel_para_entrada()


def test_entrada_casa_indisponivel_das_5_as_18():
    assert not _uc(5.0)._casa_bernardo_disponivel_para_entrada()
    assert not _uc(12.0)._casa_bernardo_disponivel_para_entrada()
    assert not _uc(17.99)._casa_bernardo_disponivel_para_entrada()


def _uc_interacao_casa(hora=18.0, estado="casa_pronta", bernardo_visivel=False):
    casa = SimpleNamespace(x=100.0, y=100.0, proprietario_bernardo=True)
    sapudo = SimpleNamespace(x=100.0, y=100.0)
    bernardo = SimpleNamespace(visivel=bernardo_visivel, x=500.0, y=500.0)
    cenario = SimpleNamespace(
        ciclo_dia_noite=SimpleNamespace(hora=hora),
        iniciar_descanso_sapudo=lambda: True,
        construcoes=[casa],
        personagens=[sapudo],
    )
    uc = ControlarConversaUseCase.__new__(ControlarConversaUseCase)
    uc.cenario = cenario
    uc.estado = estado
    uc.aberta = False
    uc.evolucao_pendente = False
    uc.bernardo = bernardo
    uc._sapudo = lambda: sapudo
    return uc


def test_prompt_casa_bernardo_aparece_mesmo_com_bernardo_recolhido():
    uc = _uc_interacao_casa(18.0, bernardo_visivel=False)
    assert uc.prompt() == "[E] Entrar / descansar"


def test_prompt_casa_bernardo_some_as_5h_mesmo_com_bernardo_recolhido():
    uc = _uc_interacao_casa(5.0, bernardo_visivel=False)
    assert uc.prompt() is None


def test_tecla_interagir_entra_na_casa_bernardo_mesmo_com_bernardo_recolhido():
    uc = _uc_interacao_casa(18.0, bernardo_visivel=False)
    assert uc.tecla_interagir() is True
    assert uc.estado == "casa_visitada"
