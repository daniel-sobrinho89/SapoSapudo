# =====================================
# entities/sapo.py
# =====================================

import math

from systems.animacoes_sapo import AnimacoesSapo
from systems.respiracao_sapo import RespiracaoSapo
from systems.ia_sapo import IASapo
from systems.system_utils import atualizar_sistemas_basicos
from datetime import datetime, timedelta
from config import *

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
        self.background_renderer = None
        self.indo_para_feira = False
        self.retornando_da_feira = False

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

    def pode_caminhar_esquerda(self):
        a = self.animacoes

        return (
            not a.andando_esquerda
            and not a.tocando_violao
            and not a.pegando_violao
            and not a.levantando_violao
            and not a.guardando_violao
            and not a.soltando_violao
            and not a.dormindo
            and not a.adormecendo
            and not a.acordando
        )

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
        a = self.animacoes

        # =====================================
        # AGENDAMENTO CAMINHADA
        # =====================================
        agora = datetime.now()
        horario_atual = (
            agora.hour,
            agora.minute
        )
        executar_caminhada = False

        # retry pendente
        if a.proxima_tentativa_caminhada:
            if (
                agora >= a.proxima_tentativa_caminhada
            ):
                executar_caminhada = True

        # horários normais
        else:
            for hora, minuto in a.horarios_caminhada:
                if horario_atual == (hora, minuto):
                    chave = (
                        agora.year,
                        agora.month,
                        agora.day,
                        hora,
                        minuto
                    )

                    if (
                        a.ultima_execucao_caminhada
                        != chave
                    ):
                        a.ultima_execucao_caminhada = chave
                        executar_caminhada = True
                        break

        if executar_caminhada:
            if self.pode_caminhar_esquerda():
                a.proxima_tentativa_caminhada = None
                a._ultimo_frame_andar = -1
                a.iniciar_andar_esquerda()
            else:
                a.proxima_tentativa_caminhada = (
                    agora + timedelta(minutes=15)
                )

        if getattr(a, "andando_esquerda", False):
            frame_atual = a.frame_andar_esquerda

            if not hasattr(a, "_ultimo_frame_andar"):
                a._ultimo_frame_andar = -1

            if frame_atual != a._ultimo_frame_andar:
                a._ultimo_frame_andar = frame_atual
                self.x -= 3.3

            # saiu pela esquerda
            if (
                not self.indo_para_feira
                and not self.background_renderer.cenario_feira
                and self.x < 0
            ):
                self.background_renderer.cenario_feira = True
                self.indo_para_feira = True
                # reaparece do lado direito
                self.x = LARGURA + 100

            if self.indo_para_feira:
                destino = (
                    LARGURA // 2
                ) + 180

                if self.x <= destino:
                    self.x = destino
                    self.indo_para_feira = False
                    a.andando_esquerda = False
                    a._ultimo_frame_andar = -1

        if violao is not None:
            if getattr(a, "guardando_violao", False):
                destino_x = getattr(violao, "x_inicial", None) - 65
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
                events["start_audio_violao"] = True
                a.iniciou_tocar_violao = False

            if getattr(a, "parar_audio_violao", False):
                events["stop_audio_violao"] = True
                a.parar_audio_violao = False

            # quando finaliza soltar violao, encapsular ação sobre o violao
            if getattr(a, "finalizou_soltar_violao", False):

                violao.acoplado = False

                violao.x = violao.x_inicial
                violao.y = violao.y_inicial

                a.finalizou_soltar_violao = False

        if getattr(a, "iniciou_andar_esquerda", False):
            events["start_audio_passeio"] = True
            a.iniciou_andar_esquerda = False

        return events
