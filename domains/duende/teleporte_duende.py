# =====================================
# domains.duende/teleporte_duende.py
# =====================================


class TeleporteDuende:
    """
    Gerencia o sistema de teleporte do Duende da Neblina.
    """

    def __init__(self):
        self.ativo = False
        self.fase = "sumindo"
        self.tempo = 0.0
        self.duracao = 0.35
        self.destino_x = 0
        self.destino_y = 0
        self.violao_alvo = None

        self.alpha_visual = 255
        self.escala_visual = 1.0

    def iniciar(self, destino_x, destino_y, violao=None):
        self.ativo = True
        self.fase = "sumindo"
        self.tempo = 0
        self.destino_x = destino_x
        self.destino_y = destino_y
        self.violao_alvo = violao

    def atualizar(self, dt, entity):
        if not self.ativo:
            return False

        self.tempo += dt
        progresso = self.tempo / self.duracao

        if self.fase == "sumindo":
            self.alpha_visual = int(255 * (1 - progresso))
            self.escala_visual = 1.0 - (progresso * 0.4)

            if progresso >= 1:
                if self.violao_alvo and self.violao_alvo.caindo:
                    violao = self.violao_alvo

                    deslocamento = (violao.velocidade_queda * self.duracao) + 90

                    entity.x = violao.x
                    entity.y = min(
                        violao.chao_y - 35,
                        violao.y + deslocamento,
                    )
                else:
                    entity.x = self.destino_x
                    entity.y = self.destino_y

                entity.resgate.iniciar()
                self.fase = "aparecendo"
                self.tempo = 0
        else:
            self.alpha_visual = int(255 * progresso)
            self.escala_visual = 0.6 + (progresso * 0.4)

            if progresso >= 1:
                self.alpha_visual = 255
                self.escala_visual = 1.0
                self.ativo = False
                self.violao_alvo = None

        return True
