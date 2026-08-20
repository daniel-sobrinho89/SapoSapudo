from core.game_config import obter_config
from domains.efeitos.entity import criar_efeitos


class MortePersonagemUseCase:
    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.entidade_alvo = None

    def iniciar(self, personagem):
        ctrl = self.cenario_principal.controladores[personagem]

        # Primeiro registramos as ações que realmente estavam usando o
        # personagem morto como alvo. Só depois cancelamos os use cases.
        # Isso preserva a informação necessária para redirecionar uma caça
        # de ovelha para a carne criada pelo drop.
        self._acoes_redirecionar = []
        controladores_envolvidos = []

        for (
            personagem_outro,
            ctrl_outro,
        ) in self.cenario_principal.controladores.items():
            if personagem_outro is personagem or ctrl_outro is None:
                continue

            alvo_encontrado = False
            obter_carne = None

            for outra_acao in ctrl_outro.get("acoes", {}).values():
                usecase = outra_acao["usecase"]
                if getattr(usecase, "entidade_alvo", None) is not personagem:
                    continue

                alvo_encontrado = True
                if usecase.__class__.__name__ == "ObterCarneUseCase":
                    obter_carne = usecase

            if not alvo_encontrado:
                continue

            if obter_carne is None:
                obter_carne = next(
                    (
                        acao["usecase"]
                        for acao in ctrl_outro.get("acoes", {}).values()
                        if acao["usecase"].__class__.__name__ == "ObterCarneUseCase"
                    ),
                    None,
                )

            if obter_carne is not None:
                obter_carne.personagem = personagem_outro
                self._acoes_redirecionar.append(obter_carne)
                controladores_envolvidos.append(ctrl_outro)

        # Só cancelamos as ações dos personagens que realmente estavam mirando
        # a ovelha morta. As demais ações do cenário permanecem intactas.
        for ctrl_envolvido in controladores_envolvidos:
            for outra_acao in ctrl_envolvido.get("acoes", {}).values():
                usecase = outra_acao["usecase"]
                cancelar = getattr(usecase, "cancelar", None)
                if cancelar is not None:
                    cancelar()
                else:
                    usecase.entidade_alvo = None

        # Limpa também as ações da própria ovelha, se houver.
        for outra_acao in ctrl["acoes"].values():
            usecase = outra_acao["usecase"]
            cancelar = getattr(usecase, "cancelar", None)
            if cancelar is not None:
                cancelar()
            else:
                usecase.entidade_alvo = None

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
            recurso = self.cenario_principal.carregar_entidade(
                drop["tipo"],
                self.entidade_alvo.x,
                self.entidade_alvo.y,
            )

            recurso.grupo_drop = self.entidade_alvo
            itens.append(recurso)

        return itens

    def _redirecionar_alvos(self, drops):
        if not drops:
            return

        for usecase in getattr(self, "_acoes_redirecionar", ()):
            personagem = getattr(usecase, "personagem", None)
            if personagem is None or personagem.vida <= 0:
                continue

            redirecionou = False
            for drop in drops:
                if self.cenario_principal.reservar_drop(drop, personagem):
                    usecase.iniciar(drop, personagem, manual=True)
                    redirecionou = True
                    break

            if not redirecionou:
                usecase.cancelar_coleta()

        self._acoes_redirecionar = []
