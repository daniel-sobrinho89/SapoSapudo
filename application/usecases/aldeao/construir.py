from domains.construcao.entity import criar_construcao


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
        construcao = criar_construcao(nome)
        construcao.x, construcao.y = pos

        cenario.construcao_arrastando = construcao

    def _arrastando_personagem(self, pos, cenario, personagem):
        if not cenario.construcao_desbloqueada(personagem):
            return

        nome = personagem.nome.removeprefix("avatar_")
        cenario.carregar_entidade(nome, *pos)

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
            cenario.construcao_arrastando = None
            cenario.personagem_arrastando = None
            return

        self._consumir_recursos(cenario)

        if cenario.construcao_arrastando is not None:
            cenario.construcoes.append(item)
            cenario.menu_construcoes.aberto = not cenario.menu_construcoes.aberto
        else:
            cenario.adicionar_personagem(item)
            cenario.menu_casa_renderer.aberto = not cenario.menu_casa_renderer.aberto

        cenario.construcao_arrastando = None
        cenario.personagem_arrastando = None

    def _consumir_recursos(self, cenario):
        novos = []

        if cenario.construcao_arrastando is not None:
            madeiras = cenario.construcao_arrastando.custo_madeira
            ouros = cenario.construcao_arrastando.custo_ouro
            carnes = cenario.construcao_arrastando.custo_carne
        else:
            madeiras = cenario.personagem_arrastando.custo_madeira
            ouros = cenario.personagem_arrastando.custo_ouro
            carnes = cenario.personagem_arrastando.custo_carne

        for renderer in cenario.renderers_recursos:
            if renderer.tipo == "madeira" and madeiras:
                madeiras -= 1
                continue

            if renderer.tipo == "ouro" and ouros:
                ouros -= 1
                continue

            if renderer.tipo == "carne" and carnes:
                carnes -= 1
                continue

            novos.append(renderer)

        cenario.renderers_recursos = novos

        for personagem in cenario.personagens:
            personagem.construcao_selecionada = None
            personagem.menu_construcoes_aberto = False
