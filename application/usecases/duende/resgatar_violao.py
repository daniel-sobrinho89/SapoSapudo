import math

from config import CHAO_Y


class ResgatarViolaoUseCase:
    MIN_TELEPORT_DIST = 120
    VELOCIDADE = 450
    VELOCIDADE_GUARDAR = 220
    OFFSET_X = 15
    OFFSET_Y = 40

    def __init__(self, duende, violao):
        self.duende = duende
        self.violao = violao
        self.animacoes = duende.animacoes
        self.violao_em_maos = False

    def executar(self):
        if not self._pode_resgatar_violao():
            return

        estado_violao = self.violao.estado()

        self.violao_em_maos = False
        distancia = abs(estado_violao.x - self.duende.x)
        self.duende.animacoes.iniciar_perseguindo_violao()

        if (
            not self._consegue_alcancar_antes_da_queda(estado_violao)
            and distancia > self.MIN_TELEPORT_DIST
        ):
            self._teleportar_para_violao()
            return

    def _consegue_alcancar_antes_da_queda(self, estado_violao):
        return self._consegue_alcancar(
            self.duende.x,
            self.duende.y,
            estado_violao,
        )

    def _teleportar_para_violao(self):
        def posicionar_no_violao(entity):
            deslocamento = (
                self.violao.velocidade_queda * entity.teleporte.duracao
            ) + 90

            entity.x = self.violao.x
            entity.y = min(
                CHAO_Y - 35,
                self.violao.y + deslocamento,
            )

        self.duende.teleportar(
            ao_teleportar=posicionar_no_violao,
            ao_finalizar=self._iniciar_resgate_monitorado,
            duracao=0.12,
            duracao_sumido=0.0,
        )

    def _iniciar_resgate_monitorado(self):
        if self.violao is not None:
            estado = self.violao.estado()
            self.violao_em_maos = False
            self.duende.alvo_x = estado.x
            self.duende.alvo_y = estado.y

    def _pode_resgatar_violao(self):
        return (
            not self.animacoes.dormindo
            and not self.animacoes.descendo_para_dormir
            and not self.duende.arrastando
            and not self.duende.animacoes.teleportando
            and not self.animacoes.ciclo_sono.dormir_por_tempo
        )

    def atualizar(self, dt):
        self._atualizar_resgate(dt)

    def _atualizar_resgate(self, dt):
        resgate_concluido = self._atualizar_resgates(dt)

        if resgate_concluido:
            self._devolver_violao()
            self._finalizar_resgate()

    def _atualizar_resgates(self, dt):
        if self.violao is None:
            return False

        if not self.violao_em_maos:
            alvo_x = self.violao.x
            alvo_y = self.violao.y

            dx = alvo_x - self.duende.x
            dy = alvo_y - self.duende.y
            distancia = math.hypot(
                alvo_x - self.duende.x,
                alvo_y - self.duende.y,
            )

            DISTANCIA_PEGAR = 18

            if distancia <= DISTANCIA_PEGAR:
                self.violao_em_maos = True
                self.animacoes.iniciar_guardando_violao()

                self.violao.caindo = False

                self.violao.x = self.duende.x + self.OFFSET_X
                self.violao.y = self.duende.y + self.OFFSET_Y

                return False

            self._mover_duende(dx, dy, distancia, dt)
            return False

        # LEVANDO PARA CASA
        destino_x = self.violao.x_inicial
        destino_y = self.violao.y_inicial

        dx = destino_x - self.duende.x
        dy = destino_y - self.duende.y
        distancia = math.hypot(dx, dy)

        if distancia < 15:
            self.violao.x = destino_x
            self.violao.y = destino_y
            return True

        velocidade = self.VELOCIDADE_GUARDAR * dt

        self.duende.x += (dx / distancia) * velocidade
        self.duende.y += (dy / distancia) * velocidade
        self.duende.base_y = self.duende.y

        # mantém o violão preso ao duende APÓS mover o duende
        self.violao.x = self.duende.x + self.OFFSET_X
        self.violao.y = self.duende.y + self.OFFSET_Y

        return False

    def _mover_duende(self, dx, dy, distancia, dt):
        velocidade = self.VELOCIDADE * dt

        self.duende.x += (dx / max(1, distancia)) * velocidade
        self.duende.y += (dy / max(1, distancia)) * velocidade
        self.duende.base_y = self.duende.y

    def _consegue_alcancar(self, duende_x, duende_y, violao):
        distancia = math.hypot(violao.x - duende_x, violao.y - duende_y)
        tempo_voo = distancia / self.VELOCIDADE

        gravidade = 900
        altura_restante = max(1, CHAO_Y - violao.y)
        velocidade_queda = max(0, violao.velocidade_queda)

        if velocidade_queda > 0:
            tempo_queda = altura_restante / velocidade_queda
        else:
            tempo_queda = math.sqrt((2 * altura_restante) / gravidade)

        tempo_queda *= 0.75
        if velocidade_queda > 250:
            tempo_queda *= 0.6

        return tempo_voo < tempo_queda

    def _devolver_violao(self):
        if self.violao is not None:
            self.violao.voltar_origem()

    def _finalizar_resgate(self):
        self.violao_em_maos = False
        self.violao.caindo = False
        self.violao.fora_do_lugar = False
        self.animacoes.iniciar_voo()

        self.duende.velocidade_x = 0
        self.duende.velocidade_y = 0
