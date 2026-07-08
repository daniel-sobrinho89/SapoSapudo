import math


class ResgatarLivroUseCase:
    MIN_TELEPORT_DIST = 120
    VELOCIDADE = 450
    VELOCIDADE_GUARDAR = 220
    OFFSET_X = 15
    OFFSET_Y = 40

    def __init__(self, duende, sapo, livro):
        self.duende = duende
        self.sapo = sapo
        self.livro = livro
        self.animacoes = duende.animacoes
        self.livro_em_maos = False

    def executar(self):
        if not self._pode_resgatar_livro():
            return

        self.livro_em_maos = False
        distancia = math.hypot(
            self.livro.x - self.duende.x,
            self.livro.y - self.duende.y,
        )
        self.duende.animacoes.iniciar_perseguindo_livro()

        if distancia > self.MIN_TELEPORT_DIST:
            self._teleportar_para_livro()
            return

    def _teleportar_para_livro(self):
        def posicionar_no_livro(entity):
            entity.x = self.livro.x
            entity.y = self.livro.y - 10
            entity.base_y = entity.y

        self.duende.teleportar(
            ao_teleportar=posicionar_no_livro,
            ao_finalizar=self._iniciar_resgate_monitorado,
            duracao=0.12,
            duracao_sumido=0.0,
        )

    def _iniciar_resgate_monitorado(self):
        if self.livro is not None:
            self.livro_em_maos = False
            self.duende.alvo_x = self.livro.x
            self.duende.alvo_y = self.livro.y

    def _pode_resgatar_livro(self):
        return (
            not self.animacoes.dormindo
            and not self.animacoes.descendo_para_dormir
            and not self.duende.arrastando
            and not self.duende.animacoes.teleportando
            and not self.animacoes.ciclo_sono.dormir_por_tempo
            and not self.livro.acoplado
            and self.livro.visivel
        )

    def atualizar(self, dt):
        self._atualizar_resgate(dt)

    def _atualizar_resgate(self, dt):
        resgate_concluido = self._atualizar_resgates(dt)

        if resgate_concluido:
            self._finalizar_resgate()

    def _atualizar_resgates(self, dt):
        if self.livro is None:
            return False

        if not self.livro_em_maos:
            alvo_x = self.livro.x
            alvo_y = self.livro.y

            dx = alvo_x - self.duende.x
            dy = alvo_y - self.duende.y
            distancia = math.hypot(
                alvo_x - self.duende.x,
                alvo_y - self.duende.y,
            )

            DISTANCIA_PEGAR = 18

            if distancia <= DISTANCIA_PEGAR:
                self.livro_em_maos = True
                self.animacoes.iniciar_guardando_livro()
                self.livro.sendo_carregado = True
                self.livro.x = self.duende.x + self.OFFSET_X
                self.livro.y = self.duende.y + self.OFFSET_Y

                return False

            self._mover_duende(
                dx,
                dy,
                distancia,
                dt,
                self.VELOCIDADE,
            )
            return False

        # LEVANDO PARA O SAPO
        destino_x = self.sapo.x
        destino_y = self.sapo.y

        dx = destino_x - self.duende.x
        dy = destino_y - self.duende.y
        distancia = math.hypot(dx, dy)

        if distancia < 15:
            self.livro.acoplar()
            self.livro.x = destino_x
            self.livro.y = destino_y
            self.sapo.animacoes.iniciar_pegar_livro()
            return True

        self._mover_duende(
            dx,
            dy,
            distancia,
            dt,
            self.VELOCIDADE_GUARDAR,
        )

        return False

    def _mover_duende(self, dx, dy, distancia, dt, velocidade):
        self.duende.x += (dx / max(1, distancia)) * velocidade * dt
        self.duende.y += (dy / max(1, distancia)) * velocidade * dt
        self.duende.base_y = self.duende.y

        if self.livro_em_maos:
            self.livro.x = self.duende.x + self.OFFSET_X
            self.livro.y = self.duende.y + self.OFFSET_Y

    # def _devolver_livro(self):
    #     if self.livro is not None:
    #         self.livro.voltar_origem()

    def _finalizar_resgate(self):
        self.livro_em_maos = False
        self.livro.flutuando = False
        self.livro.fora_do_lugar = False
        self.animacoes.iniciar_voo()

        self.duende.velocidade_x = 0
        self.duende.velocidade_y = 0
