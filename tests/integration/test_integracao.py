from tests.integration.runner import executar
from tests.integration.scenarios import SCENARIOS


def test_suite_integracao():
    resultados = [executar(nome) for nome in SCENARIOS]
    falhas = [r for r in resultados if not r.ok]
    assert not falhas, "\n\n".join(f"{r.nome}:\n{r.erro}" for r in falhas)
