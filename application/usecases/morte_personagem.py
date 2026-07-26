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

        # self.personagem_removido = False
        self.entidade_alvo = personagem
        self.poeira_grande = criar_efeitos("poeira_grande")
        self.poeira_grande.x = personagem.x
        self.poeira_grande.y = personagem.y

        self._ajustar_tamanho_poeira(self.poeira_grande, personagem)

        self.cenario_principal.adicionar_efeito(self.poeira_grande)

    # --------------------------------------------------------

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        # if self.poeira_grande.finalizado:
        #     if not self.personagem_removido:
        #         self.cenario_principal._remover_personagem(self.entidade_alvo)
        #         self._remover_personagem(self.poeira_grande)

        #     return
        # print(self.poeira_grande.animacoes.ocioso.progresso)
        # if (
        #     self.poeira_grande.animacoes.ocioso.progresso
        #     >= self.PROGRESSO_PARA_REMOVER_PERSONAGEM
        # ):
        self.cenario_principal.remover_personagem(self.entidade_alvo)
        # self.personagem_removido = True

    def _ajustar_tamanho_poeira(self, poeira, personagem):
        renderer_personagem = self.cenario_principal.obter_renderer(personagem)
        renderer_poeira_grande = self.cenario_principal.renderer_poeira_grande

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
