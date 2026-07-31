from core.game_config import obter_config
from domains.efeitos.entity import criar_efeitos


class DefenderConstrucaoUseCase:
    TEMPO_RECEBENDO_ATAQUE = 4.0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.construcao = None
        self.entidade_alvo = None
        self.tempo = 0.0
        self.fogo = None

    def iniciar(self, construcao, entidade_alvo, faccao):
        if self.entidade_alvo is None:
            self.construcao = construcao
            self.tempo = 0.0
            self.entidade_alvo = entidade_alvo

            if self.fogo is None:
                self.fogo = criar_efeitos("fogo1")
                self.fogo.x = construcao.x
                self.fogo.inicio_x = construcao.x - 30
                self.fogo.maximo_x = 10
                self.fogo.y = construcao.y + 25

                self.cenario_principal.adicionar_efeito(self.fogo)

            for personagem, ctrl in self.cenario_principal.controladores.items():
                config = obter_config(personagem.nome)

                if (
                    config.get("faccao") != faccao
                    or config.get("grupo") == "construcoes"
                ):
                    continue

                atacar = ctrl["acoes"].get("atacar")
                usecase = atacar["usecase"]

                if atacar["usecase"].entidade_alvo is None:
                    usecase.iniciar(
                        entidade_alvo,
                        personagem,
                    )

    def executar(self, dt):
        if self.fogo is not None and self.fogo.animacoes.ocioso.progresso >= 1.0:
            if self.construcao.vida == self.construcao.VIDA_MAXIMA:
                self.cenario_principal.remover_personagem(self.fogo)
                self.fogo = None
            else:
                self.fogo.animacoes.reset()

                if self.fogo.deslocamento_x > 4:
                    self.fogo.deslocamento_x = 0
                else:
                    self.fogo.deslocamento_x += 1

                self.fogo.x = self.fogo.inicio_x + self.fogo.deslocamento_x

        if self.entidade_alvo is None:
            return

        self.tempo += dt

        if self.tempo < self.TEMPO_RECEBENDO_ATAQUE:
            return

        self.tempo = 0.0
        self.entidade_alvo = None
