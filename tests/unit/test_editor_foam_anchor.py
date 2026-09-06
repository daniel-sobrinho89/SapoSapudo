from render.tilemap_renderer import TileMapRenderer


def _renderer():
    r = TileMapRenderer.__new__(TileMapRenderer)
    r.largura = 42
    r.altura = 30
    r.TIPO_GRAMA = "grama"
    r.TIPO_AGUA_FUNDO = "agua_fundo"
    r.mapa = [
        [{"tipo": r.TIPO_GRAMA} for _ in range(r.largura)] for _ in range(r.altura)
    ]
    return r


def test_espuma_lago_usa_propria_celula_de_agua():
    r = _renderer()
    r.mapa[13][27]["tipo"] = r.TIPO_AGUA_FUNDO
    r.mapa[14][27]["tipo"] = r.TIPO_AGUA_FUNDO
    # água termina na linha 14
    assert r._configurar_espuma_editor(27, 14) == (27, 14, 0, -6)


def test_espuma_lago_ao_clicar_na_grama_abaixo_ancora_na_agua():
    r = _renderer()
    r.mapa[13][27]["tipo"] = r.TIPO_AGUA_FUNDO
    r.mapa[14][27]["tipo"] = r.TIPO_AGUA_FUNDO
    assert r._configurar_espuma_editor(27, 15) == (27, 14, 0, -6)


def test_espuma_rio_inferior_usa_grama_acima():
    r = _renderer()
    r.mapa[28][27]["tipo"] = r.TIPO_GRAMA
    r.mapa[29][27]["tipo"] = r.TIPO_AGUA_FUNDO
    assert r._configurar_espuma_editor(27, 29) == (27, 28, 0, 1)


def test_espuma_rio_inferior_ao_clicar_na_grama():
    r = _renderer()
    r.mapa[28][27]["tipo"] = r.TIPO_GRAMA
    r.mapa[29][27]["tipo"] = r.TIPO_AGUA_FUNDO
    assert r._configurar_espuma_editor(27, 28) == (27, 28, 0, 1)
