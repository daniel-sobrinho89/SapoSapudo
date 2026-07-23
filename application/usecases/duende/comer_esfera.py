import math


class ComerEsferaUseCase:
    def __init__(self, duende, esferas, evento_livro):
        self.duende = duende
        self.esferas = esferas
        self.evento_livro = evento_livro

        self.tempo = 0.0
        self.esfera_alvo = None

    def executar(self, dt):
        if self.duende.animacoes.estado == self.duende.animacoes.INDO_ATRAS_ESFERA:
            self._iniciar()
        else:
            self._atualizar(dt)

    def _iniciar(self):
        self.tempo = 0.0

        esferas = [e for e in self.esferas if e.ativa and e.saiu_da_casa]

        if not esferas:
            self.esfera_alvo = None
            self.duende.animacoes.iniciar_voo()
            return

        self.esfera_alvo = min(
            esferas,
            key=lambda e: math.hypot(
                e.x - self.duende.x,
                e.y - self.duende.y,
            ),
        )

        self.duende.animacoes.iniciar_perseguindo_esfera()

    def _atualizar(self, dt):
        if self.esfera_alvo is None:
            self.duende.animacoes.iniciar_voo()
        elif self.duende.animacoes.estado == self.duende.animacoes.PERSEGUINDO_ESFERA:
            alvo_x = self.esfera_alvo.x
            alvo_y = self.esfera_alvo.y
            dx = alvo_x - self.duende.x
            dy = alvo_y - self.duende.y

            distancia = math.hypot(dx, dy)

            if distancia > 6:
                velocidade = 180
                self.duende.x += (dx / distancia) * velocidade * dt
                self.duende.y += (dy / distancia) * velocidade * dt
            else:
                self.esfera_alvo.ativa = False
                self.duende.movimento_bloqueado = True
                self.evento_livro.registrar_clique_esfera()
                self.duende.animacoes.iniciar_comer_esfera()
        elif self.duende.animacoes.estado == self.duende.animacoes.COMENDO_ESFERA:
            terminou = self.duende.animacoes.animacao_comendo_esfera.atualizar(dt)
            if terminou:
                self.duende.animacoes.iniciar_voo()
