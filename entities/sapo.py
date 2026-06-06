# =====================================
# entities/sapo.py
# =====================================

import math

from systems.animacoes_sapo import AnimacoesSapo
from systems.respiracao_sapo import RespiracaoSapo
from systems.ia_sapo import IASapo
from systems.system_utils import atualizar_sistemas_basicos

class Sapo:

    def __init__(self, x, y):

        # POSIÇÃO CENTRAL (coordenadas usadas pelo renderer)
        self.x = x
        self.y = y

        self.x_inicial = x
        self.y_inicial = y

        # MOVIMENTO (mantido por compatibilidade futura)
        self.velocidade_x = 0.0
        self.velocidade_y = 0.0

        # SYSTEMS
        self.animacoes = AnimacoesSapo()
        self.respiracao = RespiracaoSapo()
        self.ia = IASapo()

        # FLAGS mínimas
        self.acoplado_violao = False

    # métodos de delegação / API pública
    def iniciar_violao(self):
        self.animacoes.iniciar_violao()

    def parar_violao(self):
        self.animacoes.parar_violao()

    def pode_receber_violao(self):

        return (
            not getattr(self.animacoes, "iniciou_sono_hoje", False)
            and not getattr(self.animacoes, "dormindo", False)
        )

    def esta_tocando_violao(self):

        return bool(getattr(self.animacoes, "tocando_violao", False))

    # ponto central de atualização — coordena os systems relacionados ao sapo
    def atualizar(self, dt, ambiente, animacao_folha = None, violao=None):

        atualizar_sistemas_basicos(
            self.animacoes,
            self.respiracao,
            dt,
            ambiente,
            animacao_folha,
            entity=self,
        )

        # IA (decisões de alto nível)
        self.ia.obter_acao(dt)

        events = {}

        if violao is not None:
            # encapsula comportamento que antes estava em main.py
            a = self.animacoes

            # mover o sapo para guardar o violao quando apropriado
            if getattr(a, "guardando_violao", False):

                destino_x = getattr(violao, "x_inicial", None)

                frame_atual = (
                    a.frame_guardar_violao
                )

                if frame_atual != a.ultimo_frame_guardar:

                    a.ultimo_frame_guardar = (
                        frame_atual
                    )

                    if self.x < destino_x:

                        self.x = min(
                            destino_x,
                            self.x + 3.5
                        )

                        # manter o violão acompanhado ao corpo do sapo
                        violao.x = self.x + 5
                        violao.y = self.y + 20

                    else:

                        a.guardando_violao = False

                        a.soltando_violao = True

                        a.frame_soltar_violao = 0

                        a.tempo_soltar_violao = 0

                        # restaurar posição do violao quando terminado
                        violao.x = violao.x_inicial
                        violao.y = violao.y_inicial

            # eventos de áudio gerados pelos systems de animação
            if getattr(a, "iniciou_tocar_violao", False):
                events["start_audio"] = True
                a.iniciou_tocar_violao = False

            if getattr(a, "parar_audio_violao", False):
                events["stop_audio"] = True
                a.parar_audio_violao = False

            # quando finaliza soltar violao, encapsular ação sobre o violao
            if getattr(a, "finalizou_soltar_violao", False):

                violao.acoplado = False

                violao.x = violao.x_inicial
                violao.y = violao.y_inicial

                a.finalizou_soltar_violao = False

        return events
