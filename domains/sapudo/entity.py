# =====================================
# entities/sapo.py
# =====================================


from dataclasses import dataclass

from domains.sapudo.animacoes import Animacoes
from domains.sapudo.maquina_estado_sapo import EstadoSapo
from domains.sapudo.pensamentos_sapo import PensamentosSapo


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
        self.animacoes = Animacoes()
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

    def pode_caminhar(self):
        return self.animacoes.maquina.eh(EstadoSapo.PARADO)

    # ponto central de atualização — coordena os systems relacionados ao sapo
    def atualizar(self, dt):
        self.animacoes.atualizar(dt)


@dataclass
class AreaAcoplamento:
    x: float
    y: float
    raio: float

    offset_x: float = 5
    offset_y: float = 28

    def contem(self, x, y):
        return abs(x - self.x) < self.raio and abs(y - self.y) < self.raio

    def posicao_violao(self):
        return (
            self.x + self.offset_x,
            self.y + self.offset_y,
        )
