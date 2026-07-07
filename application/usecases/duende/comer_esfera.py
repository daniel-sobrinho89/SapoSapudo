import math


class ComerEsferaUseCase:
    INDO = "indo"
    COMENDO = "comendo"

    def __init__(self, duende, frasco_climatico, esferas, evento_livro):
        self.duende = duende
        self.frasco_climatico = frasco_climatico
        self.esferas = esferas
        self.evento_livro = evento_livro

        self.estado = self.INDO
        self.tempo = 0.0
        self.esfera_alvo = None

    def executar(self):
        self.estado = self.INDO
        self.tempo = 0.0

        esferas = [e for e in self.esferas if e.ativa]

        if not esferas:
            self.esfera_alvo = None
            return

        saindo = [e for e in esferas if e.saiu_do_pote]

        if saindo:
            self.esfera_alvo = min(
                saindo,
                key=lambda e: math.hypot(
                    e.x - self.duende.x,
                    e.y - self.duende.y,
                ),
            )
        else:
            self.esfera_alvo = min(
                esferas,
                key=lambda e: math.hypot(
                    e.x - self.frasco_climatico.area_pote.centerx,
                    e.y - self.frasco_climatico.area_pote.centery,
                ),
            )

        self.duende.animacoes.iniciar_perseguindo_esfera()

    def atualizar(self, dt):
        if self.esfera_alvo is None:
            self.duende.animacoes.iniciar_voo()

        if self.estado == self.INDO:
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
                self.evento_livro.registrar_clique_esfera()
                self.duende.animacoes.iniciar_comer_esfera()
                self.estado = self.COMENDO
        elif self.estado == self.COMENDO:
            terminou = self.duende.animacoes.animacao_comendo_esfera.atualizar(dt)
            if terminou:
                self.duende.animacoes.iniciar_voo()
