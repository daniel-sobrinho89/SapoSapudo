class ConstruirUseCase:
    def iniciar_arraste(self, pos, cenario, construcao=None, personagem=None):
        if construcao is not None:
            self._arrastando_construcao(pos, cenario, construcao)

    def criar_personagem_na_construcao(self, cenario, personagem, construcao):
        if personagem is None or construcao is None:
            return None

        if not cenario.personagem_desbloqueado(personagem):
            return None

        nome = personagem.nome.removeprefix("avatar_")
        x, y = cenario.obter_posicao_proxima_construcao(construcao)
        entidade = cenario.carregar_entidade(nome, x, y)

        atualizar = getattr(cenario, "_atualizar_carregamento_assets", None)
        if atualizar is not None:
            atualizar()

        self._consumir_recursos_entidade(cenario, entidade)
        cenario.menu_contextual.fechar()
        return entidade

    def _consumir_recursos_entidade(self, cenario, entidade):
        cenario.estoque["madeira"] -= getattr(entidade, "custo_madeira", 0)
        cenario.estoque["ouro"] -= getattr(entidade, "custo_ouro", 0)
        cenario.estoque["carne"] -= getattr(entidade, "custo_carne", 0)

    def _arrastando_construcao(self, pos, cenario, construcao):
        if not cenario.construcao_desbloqueada(construcao):
            return

        nome = construcao.nome.removeprefix("avatar_")
        entidade = cenario.carregar_entidade(nome, *pos)
        entidade.posicionamento_invalido = not cenario.posicao_construcao_valida(
            entidade
        )

        cenario.construcao_arrastando = entidade

    def atualizar_arraste(
        self,
        pos,
        cenario,
    ):
        item = cenario.construcao_arrastando
        if item is None:
            return
        item.x, item.y = pos
        item.posicionamento_invalido = not cenario.posicao_construcao_valida(item)

    def finalizar_arraste(
        self,
        pos,
        cenario,
    ):
        item = cenario.construcao_arrastando
        if item is None:
            return
        item.x, item.y = pos
        item.posicionamento_invalido = not cenario.posicao_construcao_valida(item)

        if item.posicionamento_invalido:
            cenario.remover_personagem(item)
            cenario.construcao_arrastando = None
            return

        self._consumir_recursos(cenario)

        cenario.menu_contextual.fechar()

        cenario.construcao_arrastando = None
        notificar = getattr(cenario, "notificar_obstaculos_alterados", None)
        if notificar is not None:
            notificar()

    def _consumir_recursos(self, cenario):
        madeiras = cenario.construcao_arrastando.custo_madeira
        ouros = cenario.construcao_arrastando.custo_ouro
        carnes = cenario.construcao_arrastando.custo_carne

        cenario.estoque["madeira"] -= madeiras
        cenario.estoque["ouro"] -= ouros
        cenario.estoque["carne"] -= carnes

        for personagem in cenario.personagens:
            personagem.construcao_selecionada = None
