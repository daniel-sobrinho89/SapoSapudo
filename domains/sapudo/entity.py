# =====================================
# entities/sapo.py
# =====================================


from dataclasses import dataclass

from domains.sapudo.animacoes import Animacoes
from domains.sapudo.maquina_estado_sapo import EstadoSapo
from domains.sapudo.pensamentos_sapo import PensamentosSapo


class Sapo:
    def __init__(self, x, y, spotify, clima_service):
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
        self.background_renderer = None
        self.spotify = spotify
        self.clima = clima_service

    # métodos de delegação / API pública
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
