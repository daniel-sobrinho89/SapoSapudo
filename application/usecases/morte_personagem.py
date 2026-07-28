from core.game_config import obter_config
from domains.efeitos.entity import criar_efeitos


class MortePersonagemUseCase:
    PROGRESSO_PARA_REMOVER_PERSONAGEM = 0.1

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.entidade_alvo = None

    def iniciar(self, personagem):
        ctrl = self.cenario_principal.controladores[personagem]
        for outra_acao in ctrl["acoes"].values():
            outra_acao["usecase"].entidade_alvo = None

        self.entidade_alvo = personagem
        self.poeira_grande = criar_efeitos("poeira_grande")
        self.poeira_grande.x = personagem.x
        self.poeira_grande.y = personagem.y

        self._ajustar_tamanho_poeira(self.poeira_grande, personagem)

        self.cenario_principal.adicionar_efeito(self.poeira_grande)

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        drops = self._dropar_itens()
        self._redirecionar_alvos(drops)

        self.cenario_principal.remover_personagem(self.entidade_alvo)

    def _ajustar_tamanho_poeira(self, poeira, personagem):
        renderer_personagem = self.cenario_principal.renderers.get(personagem.nome)
        renderer_poeira_grande = self.cenario_principal.renderers.get("poeira_grande")

        frame_personagem = renderer_personagem.obter_frame_animacao(
            personagem.animacoes
        )
        frame_poeira = renderer_poeira_grande.obter_frame_animacao(poeira.animacoes)

        if frame_personagem is None or frame_poeira is None:
            return

        corpo_personagem = frame_personagem.get_bounding_rect()
        corpo_poeira = frame_poeira.get_bounding_rect()

        poeira.escala_x = (
            corpo_personagem.w
            * renderer_personagem.escala
            / (corpo_poeira.w * renderer_poeira_grande.escala)
        )
        poeira.escala_y = (
            corpo_personagem.h
            * renderer_personagem.escala
            / (corpo_poeira.h * renderer_poeira_grande.escala)
        )

        centro_personagem_x = (
            personagem.x
            + (
                corpo_personagem.x
                + corpo_personagem.w / 2
                - frame_personagem.get_width() / 2
            )
            * renderer_personagem.escala
        )
        centro_personagem_y = (
            personagem.y
            + (
                corpo_personagem.y
                + corpo_personagem.h / 2
                - frame_personagem.get_height() / 2
            )
            * renderer_personagem.escala
        )

        centro_poeira_x = (
            (corpo_poeira.x + corpo_poeira.w / 2 - frame_poeira.get_width() / 2)
            * renderer_poeira_grande.escala
            * poeira.escala_x
        )
        centro_poeira_y = (
            (corpo_poeira.y + corpo_poeira.h / 2 - frame_poeira.get_height() / 2)
            * renderer_poeira_grande.escala
            * poeira.escala_y
        )

        poeira.x = centro_personagem_x - centro_poeira_x
        poeira.y = centro_personagem_y - centro_poeira_y

    def _dropar_itens(self):
        config = obter_config(self.entidade_alvo.nome)

        drop = config.get("drop")
        if not drop:
            return []

        itens = []

        for _ in range(drop.get("quantidade", 1)):
            itens.append(
                self.cenario_principal.carregar_entidade(
                    drop["tipo"],
                    self.entidade_alvo.x,
                    self.entidade_alvo.y,
                )
            )

        return itens

    def _redirecionar_alvos(self, drops):
        if not drops:
            return

        for ctrl in self.cenario_principal.controladores.values():
            for acao in ctrl["acoes"].values():
                usecase = acao["usecase"]

                if usecase.entidade_alvo is not self.entidade_alvo:
                    continue

                if usecase.__class__.__name__ != "ObterCarneUseCase":
                    continue

                for drop in drops:
                    if self.cenario_principal.reservar_drop(
                        drop,
                        usecase.personagem,
                    ):
                        usecase.iniciar(drop, usecase.personagem)
                        break
                else:
                    usecase.cancelar()
