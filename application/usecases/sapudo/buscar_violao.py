from domains.sapudo.maquina_estado_sapo import EstadoSapo


class BuscarViolaoUseCase:
    def __init__(
        self,
        violao,
        sapo,
    ):
        self.violao = violao
        self.sapo = sapo

        self.em_execucao = False

    def executar(self):
        animacoes = self.sapo.animacoes

        if (
            self.em_execucao
            or not self.sapo.pode_caminhar()
            or animacoes.maquina.esta_com_violao()
            or self.violao.acoplado
            or not self.sapo.pode_receber_violao()
        ):
            return

        self.em_execucao = True

        if self.sapo.x < self.violao.x:
            animacoes.iniciar_andar_direita()
        else:
            animacoes.iniciar_andar_esquerda()

    def atualizar(self):
        if not self.em_execucao:
            return

        animacoes = self.sapo.animacoes

        if not animacoes.maquina.em_estado(
            EstadoSapo.ANDANDO_DIREITA,
            EstadoSapo.ANDANDO_ESQUERDA,
        ):
            self.em_execucao = False
            return

        if abs(self.sapo.x - self.violao.x) > self.sapo.distancia_violao:
            return

        self.em_execucao = False
        animacoes.maquina.trocar(EstadoSapo.CHEGOU_AO_VIOLAO)
