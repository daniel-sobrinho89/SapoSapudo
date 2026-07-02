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
        self.duracao_sumido = 1.5
        self.destino_x = 0
        self.destino_y = 0
        self.ao_teleportar = None
        self.finalizar_callback = None
        self.tempo_sumido = 0.0
        self.alpha_visual = 255
        self.escala_visual = 1.0

    def iniciar(
        self,
        destino_x=None,
        destino_y=None,
        ao_teleportar=None,
        ao_finalizar=None,
        duracao=None,
        duracao_sumido=None,
    ):
        self.ativo = True
        self.fase = "sumindo"
        self.tempo = 0
        self.destino_x = destino_x
        self.destino_y = destino_y
        self.ao_teleportar = ao_teleportar
        self.finalizar_callback = ao_finalizar
        self.alpha_visual = 255
        self.escala_visual = 1.0
        self.duracao = duracao if duracao is not None else self.duracao
        self.duracao_sumido = (
            duracao_sumido if duracao_sumido is not None else self.duracao_sumido
        )

    def atualizar(self, dt, entity):
        if not self.ativo:
            return False

        self.tempo += dt
        progresso = self.tempo / self.duracao

        if self.fase == "sumindo":
            self.alpha_visual = int(255 * (1 - progresso))
            self.escala_visual = 1.0 - (progresso * 0.4)

            if progresso >= 1:
                if self.ao_teleportar:
                    self.ao_teleportar(entity)
                elif self.destino_x is not None:
                    entity.x = self.destino_x
                    entity.y = self.destino_y
                else:
                    entity.x = self.destino_x
                    entity.y = self.destino_y

                self.fase = "sumido"
                self.tempo = 0
                self.tempo_sumido = 0

            return False
        elif self.fase == "sumido":
            self.tempo_sumido += dt

            if self.tempo_sumido >= self.duracao_sumido:
                self.fase = "aparecendo"
                self.tempo = 0

            return False
        elif self.fase == "aparecendo":
            self.alpha_visual = int(255 * progresso)
            self.escala_visual = 0.6 + (progresso * 0.4)

            if progresso >= 1:
                self.alpha_visual = 255
                self.escala_visual = 1.0
                self.ativo = False

                if self.finalizar_callback:
                    self.finalizar_callback()

                self.ao_teleportar = None
                self.finalizar_callback = None
                return True

            return False

        self.alpha_visual = int(255 * progresso)
        self.escala_visual = 0.6 + (progresso * 0.4)

        # if progresso >= 1:
        #     self.alpha_visual = 255
        #     self.escala_visual = 1.0
        #     self.ativo = False
        #     self.ao_teleportar = None

        #     return True

        return False
