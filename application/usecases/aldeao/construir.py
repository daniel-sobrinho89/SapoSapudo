class ConstruirUseCase:
    def iniciar_arraste(self, pos, cenario, construcao=None, personagem=None):
        if construcao is not None:
            self._arrastando_construcao(pos, cenario, construcao)
        else:
            self._arrastando_personagem(pos, cenario, personagem)

    def _arrastando_construcao(self, pos, cenario, construcao):
        if not cenario.construcao_desbloqueada(construcao):
            return

        nome = construcao.nome.removeprefix("avatar_")
        entidade = cenario.carregar_entidade(nome, *pos)

        cenario.construcao_arrastando = entidade

    def _arrastando_personagem(self, pos, cenario, personagem):
        if not cenario.construcao_desbloqueada(personagem):
            return

        nome = personagem.nome.removeprefix("avatar_")
        entidade = cenario.carregar_entidade(nome, *pos)

        cenario.personagem_arrastando = entidade

    def atualizar_arraste(
        self,
        pos,
        cenario,
    ):
        if cenario.construcao_arrastando is not None:
            item = cenario.construcao_arrastando
        else:
            item = cenario.personagem_arrastando

        if item is None:
            return

        item.x, item.y = pos

    def finalizar_arraste(
        self,
        pos,
        cenario,
    ):
        if cenario.construcao_arrastando is not None:
            item = cenario.construcao_arrastando
        else:
            item = cenario.personagem_arrastando

        if item is None:
            return

        item.x, item.y = pos

        if not cenario.tilemap.eh_grama(
            item.x,
            item.y,
        ):
            personagem = cenario.construcao_arrastando or cenario.personagem_arrastando
            cenario.remover_personagem(personagem)
            cenario.construcao_arrastando = None
            cenario.personagem_arrastando = None
            return

        self._consumir_recursos(cenario)

        cenario.menu_construcoes.aberto = False
        cenario.menu_casa_renderer.aberto = False

        cenario.construcao_arrastando = None
        cenario.personagem_arrastando = None

    def _consumir_recursos(self, cenario):
        if cenario.construcao_arrastando is not None:
            madeiras = cenario.construcao_arrastando.custo_madeira
            ouros = cenario.construcao_arrastando.custo_ouro
            carnes = cenario.construcao_arrastando.custo_carne
        else:
            madeiras = cenario.personagem_arrastando.custo_madeira
            ouros = cenario.personagem_arrastando.custo_ouro
            carnes = cenario.personagem_arrastando.custo_carne

        cenario.estoque["madeira"] -= madeiras
        cenario.estoque["ouro"] -= ouros
        cenario.estoque["carne"] -= carnes

        for personagem in cenario.personagens:
            personagem.construcao_selecionada = None
            personagem.menu_construcoes_aberto = False
