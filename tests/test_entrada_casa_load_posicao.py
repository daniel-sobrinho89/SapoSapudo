from types import SimpleNamespace

from application.usecases.conversa.controlar_conversa import ControlarConversaUseCase


class FakeCasa:
    nome = "casa_palha_azul"
    proprietario_bernardo = True
    visivel = True
    x = 288.0
    y = 356.0


class FakeCenario:
    def __init__(self):
        self.construcoes = []
        self.ciclo_dia_noite = SimpleNamespace(hora=19.25)
        self.personagens = [SimpleNamespace(nome="sapudo", x=300.0, y=356.0)]
        self.sapudo = self.personagens[0]
        self.estoque = {"madeira": 0}

    def carregar_entidade(self, tipo, x=None, y=None, altura=None):
        assert tipo == "casa_palha_azul"
        casa = FakeCasa()
        casa.x, casa.y = x, y
        return casa

    def adicionar_personagem(self, entidade, nome_lista):
        getattr(self, nome_lista).append(entidade)

    def notificar_obstaculos_alterados(self):
        pass


def test_casa_pronta_reconstroi_casa_apos_load_e_aparece_no_prompt():
    c = FakeCenario()
    cc = ControlarConversaUseCase(c)
    cc.estado = "casa_pronta"
    cc.casa_fase = "pronta"
    cc.casa_posicao = (288.0, 356.0)

    assert cc.prompt() == "[E] Entrar / descansar"
    assert len(c.construcoes) == 1
    assert c.construcoes[0].proprietario_bernardo is True
