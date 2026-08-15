from core.game_config import obter_config
from domains.efeitos.entity import criar_efeitos


class DefenderConstrucaoUseCase:
    TEMPO_RECEBENDO_ATAQUE = 4.0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.construcao = None
        self.entidade_alvo = None
        self.tempo = 0.0
        self.fogos = []

    def iniciar(self, construcao, entidade_alvo, faccao):
        if self.entidade_alvo is None:
            self.construcao = construcao

            self.tempo = 0.0
            self.entidade_alvo = entidade_alvo

            self._atualizar_fogos()

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
        self._atualizar_fogos()

        if self.entidade_alvo is None:
            return

        self.tempo += dt

        if self.tempo < self.TEMPO_RECEBENDO_ATAQUE:
            return

        self.tempo = 0.0
        self.entidade_alvo = None

    def _atualizar_fogos(self):
        if self.construcao is None:
            return

        vida_maxima = self.construcao.VIDA_MAXIMA
        vida_atual = max(0, self.construcao.vida)

        percentual = vida_atual / vida_maxima if vida_maxima > 0 else 0

        quantidade_fogo1 = 0
        quantidade_fogo2 = 0

        if percentual < 1.0 and percentual >= 0.75:
            quantidade_fogo1 = 1

        elif percentual < 0.75 and percentual >= 0.50:
            quantidade_fogo1 = 2

        elif percentual < 0.50 and percentual >= 0.25:
            quantidade_fogo1 = 2
            quantidade_fogo2 = 1

        elif percentual < 0.25:
            quantidade_fogo1 = 2
            quantidade_fogo2 = 2

        quantidade_desejada = quantidade_fogo1 + quantidade_fogo2

        while len(self.fogos) > quantidade_desejada:
            fogo = self.fogos.pop()
            self.cenario_principal.remover_personagem(fogo)

        while len(self.fogos) < quantidade_desejada:
            indice = len(self.fogos)

            if indice < quantidade_fogo1:
                fogo = criar_efeitos("fogo1")
            else:
                fogo = criar_efeitos("fogo2")

            fogo.persistente = True
            fogo.construcao_origem = self.construcao

            deslocamentos = [
                (-30, 25),
                (20, 35),
                (-5, 15),
                (35, 20),
            ]

            deslocamento_x, deslocamento_y = deslocamentos[indice % len(deslocamentos)]

            fogo.x = self.construcao.x + deslocamento_x
            fogo.y = self.construcao.y + deslocamento_y

            self.cenario_principal.adicionar_efeito(fogo)
            self.fogos.append(fogo)
