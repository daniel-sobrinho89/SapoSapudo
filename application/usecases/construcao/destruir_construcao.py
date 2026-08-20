from core.game_config import obter_config
from domains.efeitos.entity import criar_efeitos


class DestruirConstrucaoUseCase:
    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.entidade_alvo = None

    def iniciar(self, personagem):
        ctrl = self.cenario_principal.controladores[personagem]
        for outra_acao in ctrl["acoes"].values():
            outra_acao["usecase"].entidade_alvo = None

        self.entidade_alvo = personagem
        self.explosao = criar_efeitos("explosao2")
        self.explosao.x = personagem.x
        self.explosao.y = personagem.y

        self._ajustar_tamanho_efeito(self.explosao, personagem)
        self.cenario_principal.adicionar_efeito(self.explosao)

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        self._remover_fogos()

        self._dropar_itens()
        self.cenario_principal.remover_personagem(self.entidade_alvo)

    def _ajustar_tamanho_efeito(self, explosao, personagem):
        renderer_personagem = self.cenario_principal.renderers.get(personagem.nome)
        renderer_explosao = self.cenario_principal.renderers.get("explosao2")

        frame_personagem = renderer_personagem.obter_frame_animacao(
            personagem.animacoes
        )
        frame_efeito = renderer_explosao.obter_frame_animacao(explosao.animacoes)

        if frame_personagem is None or frame_efeito is None:
            return

        corpo_entidade = frame_personagem.get_bounding_rect()
        corpo_efeito = frame_efeito.get_bounding_rect()

        centro_personagem_x = (
            personagem.x
            + (
                corpo_entidade.x
                + corpo_entidade.w / 2
                - frame_personagem.get_width() / 2
            )
            * renderer_personagem.escala
        )
        centro_personagem_y = (
            personagem.y
            + (
                corpo_entidade.y
                + corpo_entidade.h / 2
                - frame_personagem.get_height() / 2
            )
            * renderer_personagem.escala
        )

        centro_efeito_x = (
            corpo_efeito.x + corpo_efeito.w / 2 - frame_efeito.get_width() / 2
        ) * renderer_explosao.escala
        centro_efeito_y = (
            corpo_efeito.y + corpo_efeito.h / 2 - frame_efeito.get_height() / 2
        ) * renderer_explosao.escala

        explosao.x = centro_personagem_x - centro_efeito_x
        explosao.y = centro_personagem_y - centro_efeito_y

    def _remover_fogos(self):
        if self.entidade_alvo is None:
            return

        for fogo in self.cenario_principal.efeitos[:]:
            if getattr(fogo, "construcao_origem", None) is self.entidade_alvo:
                self.cenario_principal.efeitos.remove(fogo)

    def _dropar_itens(self):
        config = obter_config(self.entidade_alvo.nome)

        drop = config.get("drop")
        if not drop:
            return []

        for _ in range(drop.get("quantidade", 1)):
            recurso = self.cenario_principal.carregar_entidade(
                drop["tipo"],
                self.entidade_alvo.x,
                self.entidade_alvo.y,
            )
            recurso.grupo_drop = self.entidade_alvo
