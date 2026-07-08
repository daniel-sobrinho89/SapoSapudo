from types import SimpleNamespace

from application.usecases.sapudo.controlar_comportamento_sapo import (
    ControlarComportamentoSapoUseCase,
)
from domains.clima.livro_climatico import LivroClimatico
from domains.sapudo.maquina_estado_sapo import EstadoSapo


class FakeTTS:
    def __init__(self):
        self.textos = []

    def falar(self, texto):
        self.textos.append(texto)


class FakeLivroClimatico:
    def __init__(self):
        self.textos = []

    def gerar_texto_narracao(self, clima_service):
        self.textos.append(getattr(clima_service, "temperature", None))
        return "texto de narração"


class FakeMachine:
    def __init__(self, estado):
        self.estado = estado

    def eh(self, estado):
        return self.estado == estado

    def em_estado(self, *estados):
        return self.estado in estados

    def trocar(self, novo_estado):
        self.estado = novo_estado


def _criar_usecase(machine, tts, livro_climatico):
    sapo = SimpleNamespace(
        controle_esquerda=False,
        controle_direita=False,
        indo_para_feira=False,
        comando_ir_feira=False,
        andar_iniciado_por_controle=False,
        x=0,
        background_renderer=SimpleNamespace(cenario_feira=False),
    )
    sapo.pode_caminhar = lambda: True

    animacoes = SimpleNamespace(
        maquina=machine,
        pegar_livro=SimpleNamespace(frame=0, total_frames=10),
        acordar=SimpleNamespace(atualizar=lambda dt: False),
        dormir=SimpleNamespace(atualizar=lambda dt: False),
        iniciar_andar_esquerda=lambda: None,
        iniciar_andar_direita=lambda: None,
        iniciar_acordar=lambda: None,
        iniciar_dormir=lambda: None,
    )
    sapo.animacoes = animacoes

    return ControlarComportamentoSapoUseCase(
        sapo=sapo,
        violao=None,
        spotify=SimpleNamespace(spotify_tocando_cache=False),
        audio=SimpleNamespace(tocar_passeio_sapudo=lambda: None),
        clima_service=SimpleNamespace(temperature=18),
        livro_climatico=livro_climatico,
        tts_service=tts,
    )


def test_gerar_texto_narracao_usa_dados_do_clima():
    livro = LivroClimatico()
    clima = SimpleNamespace(
        temperature=18,
        humidity=85,
        wind_speed=25,
        wind_direction=180,
        cloudiness=60,
        future_cloudiness_3h=80,
    )

    texto = livro.gerar_texto_narracao(clima)

    assert isinstance(texto, str)
    assert texto
    assert "Hum" in texto or "lago" in texto.lower() or "vento" in texto.lower()


def test_usecase_dispara_narracao_apenas_na_primeira_entrada_em_lendo_livro():
    machine = FakeMachine(EstadoSapo.PARADO)
    tts = FakeTTS()
    livro_climatico = FakeLivroClimatico()
    usecase = _criar_usecase(machine, tts, livro_climatico)

    machine.estado = EstadoSapo.LENDO_LIVRO
    usecase.executar(0.0)
    assert tts.textos == ["texto de narração"]

    usecase.executar(0.0)
    assert tts.textos == ["texto de narração"]

    machine.estado = EstadoSapo.PARADO
    usecase.executar(0.0)

    machine.estado = EstadoSapo.LENDO_LIVRO
    usecase.executar(0.0)
    assert tts.textos == ["texto de narração", "texto de narração"]
