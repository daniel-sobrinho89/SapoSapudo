import math


class EsconderAtrasViolaoUseCase:
    INDO = "indo"
    ENCOLHENDO = "encolhendo"
    ESCONDIDO = "escondido"
    SAINDO = "saindo"

    def __init__(self, duende, violao):
        self.duende = duende
        self.violao = violao

        self.estado = self.INDO
        self.tempo = 0.0

        self.escala_inicial = duende.escala_visual
        self.escala_final = 0.55

        self.offset_y = 0
        self.saindo_x = 0
        self.saindo_y = 0
        self.saindo_offset_x = 0
        self.saindo_offset_y = 0

    def executar(self):
        self.estado = self.INDO
        self.tempo = 0.0
        self.offset_y = 0
        self.duende.escala_visual = 1.0
        self.duende.animacoes.iniciar_escondendo_atras_violao()

    def atualizar(self, dt):
        self.tempo += dt

        if self.estado == self.INDO:
            alvo_x = self.violao.x - 20
            alvo_y = self.violao.y - 55

            dx = alvo_x - self.duende.x
            dy = alvo_y - self.duende.y

            distancia = math.hypot(dx, dy)

            if distancia > 2:
                velocidade = 90

                self.duende.x += (dx / distancia) * velocidade * dt
                self.duende.y += (dy / distancia) * velocidade * dt
            else:
                self.duende.x = alvo_x
                self.duende.y = alvo_y

                self.estado = self.ENCOLHENDO
                self.tempo = 0
                self.offset_y = (self.duende.y + 40) - self.violao.y

        elif self.estado == self.ENCOLHENDO:
            self.duende.movimento_bloqueado = True
            progresso = min(self.tempo / 0.35, 1.0)
            self.duende.escala_visual = (
                self.escala_inicial
                + (self.escala_final - self.escala_inicial) * progresso
            )

            if progresso >= 1:
                self.estado = self.ESCONDIDO
                self.tempo = 0.0
        elif self.estado == self.ESCONDIDO:
            self.duende.x = self.violao.x - 20
            base_y = self.violao.y + self.offset_y
            ciclo = self.tempo % 2.4

            if ciclo < 0.18:
                # sobe rapidamente
                t = ciclo / 0.18
                self.duende.y = base_y - (18 * t)
            elif ciclo < 0.75:
                # fica espiando
                self.duende.y = base_y - 18
            elif ciclo < 0.93:
                # desce rapidamente
                t = (ciclo - 0.75) / 0.18
                self.duende.y = base_y - 18 + (18 * t)
            else:
                # permanece escondido por mais tempo
                self.duende.y = base_y

            if self.tempo >= 6:
                self.estado = self.SAINDO
                self.tempo = 0.0
                self.saindo_offset_x = self.duende.x - self.violao.x
                self.saindo_offset_y = self.duende.y - self.violao.y
        elif self.estado == self.SAINDO:
            progresso = min(self.tempo / 0.70, 1.0)
            progresso = 1 - (1 - progresso) ** 3

            inicio_x = self.violao.x + self.saindo_offset_x
            inicio_y = self.violao.y + self.saindo_offset_y
            destino_x = self.violao.x - 35
            destino_y = self.violao.y - 95

            self.duende.x = inicio_x + (destino_x - inicio_x) * progresso
            self.duende.y = inicio_y + (destino_y - inicio_y) * progresso

            self.duende.escala_visual = (
                self.escala_final + (1.0 - self.escala_final) * progresso
            )

            if progresso >= 1:
                self.duende.movimento_bloqueado = False
                self.duende.escala_visual = 1.0
                self.duende.animacoes.iniciar_voo()
