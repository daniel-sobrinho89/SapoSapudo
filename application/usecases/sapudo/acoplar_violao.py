from domains.sapudo.maquina_estado_sapo import EstadoSapo


class AcoplarViolaoUseCase:
    def __init__(self, violao, sapo, duende, spotify):
        self.violao = violao
        self.sapo = sapo
        self.duende = duende
        self.spotify = spotify

    def executar(self, area):
        if not self.violao.arrastando:
            return False

        maquina = self.sapo.animacoes.maquina

        self.violao.finalizar_arraste()

        if (
            not area.contem(
                self.violao.x,
                self.violao.y,
            )
            or self.sapo.animacoes.maquina.esta_com_livro()
        ):
            self.violao.iniciar_queda()
            return True

        (
            self.violao.x,
            self.violao.y,
        ) = area.posicao_violao()

        self.spotify.tocar()
        self.violao.acoplado = True
        maquina.trocar(EstadoSapo.CHEGOU_AO_VIOLAO)
        return True
