# =====================================
# entities/sapo.py
# =====================================


from dataclasses import dataclass
from datetime import datetime, timedelta

from config import LARGURA
from domains.sapudo.animacoes_sapo import AnimacoesSapo
from domains.sapudo.ia_sapo import IASapo
from domains.sapudo.maquina_estado_sapo import EstadoSapo
from domains.sapudo.pensamentos_sapo import PensamentosSapo
from domains.sapudo.respiracao_sapo import RespiracaoSapo


class Sapo:
    def __init__(self, x, y, violao, spotify, distancia_violao, clima_service):
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
        self.pensamentos = PensamentosSapo()
        self.controle_esquerda = False
        self.controle_direita = False
        self.andando_manual = False
        self.andar_iniciado_por_controle = False
        self.andar_iniciado_por_spotify = False

        # FLAGS mínimas
        self.acoplado_violao = False
        self.background_renderer = None
        self.indo_para_feira = False
        self.retornando_da_feira = False
        self.comando_ir_feira = False
        self.violao = violao
        self.spotify = spotify
        self.distancia_violao = distancia_violao
        self.clima = clima_service

    def ir_para_feira(self):
        """Inicia o deslocamento para a feira."""
        self.comando_ir_feira = True
        self.andar_iniciado_por_controle = False
        if self.pode_caminhar():
            self.animacoes.proxima_tentativa_caminhada = None
            self.animacoes._ultimo_frame_andar = -1
            self.animacoes.iniciar_andar_esquerda()

    def area_violao(self):
        return AreaAcoplamento(
            x=self.x,
            y=self.y,
            raio=80,
        )

    # métodos de delegação / API pública
    def pode_receber_violao(self):
        return not self.animacoes.maquina.em_estado(
            EstadoSapo.DORMINDO, EstadoSapo.ADORMECENDO
        )

    def esta_tocando_violao(self):
        return self.animacoes.maquina.eh(EstadoSapo.TOCANDO_VIOLAO)

    def iniciar_controle_esquerda(self):
        if not self.pode_caminhar():
            return

        self.andando_manual = True
        self.controle_esquerda = True
        self.andar_iniciado_por_controle = True

        if not self.animacoes.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            self.animacoes.iniciar_andar_esquerda()

    def parar_controle_esquerda(self):
        self.andando_manual = False
        self.controle_esquerda = False
        if self.animacoes.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            self.animacoes.maquina.trocar(EstadoSapo.PARADO)

    def iniciar_controle_direita(self):
        if not self.pode_caminhar():
            return

        self.andando_manual = True
        self.controle_direita = True
        self.andar_iniciado_por_controle = True

        if not self.animacoes.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            self.animacoes.iniciar_andar_direita()

    def parar_controle_direita(self):
        self.andando_manual = False
        self.controle_direita = False
        if self.animacoes.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            self.animacoes.maquina.trocar(EstadoSapo.PARADO)

    def pode_caminhar(self):
        return self.animacoes.maquina.eh(EstadoSapo.PARADO)

    # ponto central de atualização — coordena os systems relacionados ao sapo
    def atualizar(self, dt):
        self.animacoes.atualizar(dt)

        events = {}
        a = self.animacoes

        acao = self.ia.obter_acao(dt, self)

        if acao:
            texto = self.pensamentos.executar(acao)

            if texto:
                events["novo_pensamento"] = texto

        # =====================================
        # AGENDAMENTO CAMINHADA
        # =====================================
        agora = datetime.now()
        horario_atual = (agora.hour, agora.minute)
        executar_caminhada = False

        if self.controle_esquerda and not self.indo_para_feira:
            self.x -= 4
            if self.background_renderer.cenario_feira and self.x <= 0:
                self.x = 0

        if self.controle_direita:
            self.x += 4

            if self.background_renderer.cenario_feira:
                if self.x > LARGURA:
                    excesso = self.x - LARGURA

                    self.background_renderer.cenario_feira = False
                    self.x = excesso

            else:
                if self.x > LARGURA:
                    self.x = LARGURA

        # retry pendente
        if a.proxima_tentativa_caminhada:
            if agora >= a.proxima_tentativa_caminhada:
                executar_caminhada = True

        # horários normais
        else:
            for hora, minuto in a.horarios_caminhada:
                if horario_atual == (hora, minuto):
                    chave = (agora.year, agora.month, agora.day, hora, minuto)

                    if a.ultima_execucao_caminhada != chave:
                        a.ultima_execucao_caminhada = chave
                        executar_caminhada = True
                        break

        if executar_caminhada:
            self.andar_iniciado_por_controle = False
            if self.pode_caminhar():
                a.proxima_tentativa_caminhada = None
                a._ultimo_frame_andar = -1
                a.iniciar_andar_esquerda()
            else:
                a.proxima_tentativa_caminhada = agora + timedelta(minutes=15)

        if a.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            frame_atual = a.andar_esquerda.frame

            if not hasattr(a, "_ultimo_frame_andar"):
                a._ultimo_frame_andar = -1

            if frame_atual != a._ultimo_frame_andar:
                a._ultimo_frame_andar = frame_atual
                self.x -= 4

            if (
                self.x < 0
                and (self.comando_ir_feira or not self.indo_para_feira)
                and not self.background_renderer.cenario_feira
            ):
                self.background_renderer.cenario_feira = True
                self.indo_para_feira = True

                self.x = LARGURA + 100
                self.comando_ir_feira = False

            if self.indo_para_feira:
                destino = (LARGURA // 2) + 180

                if self.x <= destino:
                    self.x = destino

                    self.indo_para_feira = False
                    self.comando_ir_feira = False

                    self.controle_esquerda = False
                    self.andando_manual = False

                    a.maquina.trocar(EstadoSapo.PARADO)

                    a._ultimo_frame_andar = -1

        if a.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            frame_atual = a.andar_direita.frame

            if not hasattr(a, "_ultimo_frame_andar_direita"):
                a._ultimo_frame_andar_direita = -1

            if frame_atual != a._ultimo_frame_andar_direita:
                a._ultimo_frame_andar_direita = frame_atual

                self.x += 4

            # eventos de áudio gerados pelos systems de animação
            if getattr(a, "iniciou_tocar_violao", False):
                events["start_audio_violao"] = True
                a.iniciou_tocar_violao = False

            if getattr(a, "parar_audio_violao", False):
                events["stop_audio_violao"] = True
                a.parar_audio_violao = False

            # quando finaliza soltar violao, encapsular ação sobre o violao
            if getattr(a, "finalizou_soltar_violao", False):
                self.violao.voltar_origem()

                a.finalizou_soltar_violao = False

        if getattr(a, "iniciou_andar_esquerda", False):
            if (
                not self.andar_iniciado_por_controle
                and not self.andar_iniciado_por_spotify
            ):
                events["start_audio_passeio"] = True

            a.iniciou_andar_esquerda = False

        return events


@dataclass
class AreaAcoplamento:
    x: float
    y: float
    raio: float

    offset_x: float = 5
    offset_y: float = 20

    def contem(self, x, y):
        return abs(x - self.x) < self.raio and abs(y - self.y) < self.raio

    def posicao_violao(self):
        return (
            self.x + self.offset_x,
            self.y + self.offset_y,
        )
