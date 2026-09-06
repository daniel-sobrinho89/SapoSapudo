class EvolucaoSapudoUseCase:
    """Regras simples de experiência e distribuição de pontos do Sapudo."""

    # O primeiro nível exige 100 XP; cada nível seguinte exige mais 100 XP.
    # Assim a progressão não dispara cedo demais quando uma missão concede
    # vários inimigos em sequência.
    XP_BASE = 100

    def xp_necessario_para_nivel(self, nivel):
        nivel = max(1, int(nivel))
        return self.XP_BASE * nivel

    def adicionar_experiencia(self, sapudo, quantidade):
        if sapudo is None or quantidade <= 0:
            return False
        sapudo.experiencia += quantidade
        sapudo.experiencia_total += quantidade

        while sapudo.experiencia >= self.xp_necessario_para_nivel(sapudo.nivel):
            sapudo.experiencia -= self.xp_necessario_para_nivel(sapudo.nivel)
            sapudo.nivel += 1
            sapudo.pontos_evolucao += 1
        return True

    def aplicar_ponto(self, sapudo, atributo):
        if sapudo is None or sapudo.pontos_evolucao <= 0:
            return False
        if atributo == "ataque":
            sapudo.ataque += 1
        elif atributo == "defesa":
            sapudo.defesa += 1
        else:
            return False
        sapudo.pontos_evolucao -= 1
        return True
