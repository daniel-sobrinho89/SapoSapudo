import math
from datetime import datetime


class Ambiente:
    """
    Representa o estado global do ambiente no jogo, incluindo tempo, vento,
    ciclo dia/noite e clima.
    """

    def __init__(self):
        self.tempo = 0
        self.vento = 0

    def atualizar(self, dt, clima_service=None):
        self.tempo += dt

        # Cálculo base do vento (oscilações naturais)
        vento_lento = math.sin(self.tempo * 0.15)
        micro_vento = math.sin(self.tempo * 1.4) * 0.18
        rajada = math.sin(self.tempo * 0.05) * 0.7

        self.vento = vento_lento + micro_vento + rajada

        # Influência do clima externo (serviço de clima)
        if clima_service:
            direcao_rad = math.radians(clima_service.wind_direction + 180)
            sinal_direcao = math.sin(direcao_rad)
            influencia_clima = sinal_direcao * clima_service.wind_speed * 0.15

            if getattr(clima_service, "rajada_ativa", False):
                influencia_clima += sinal_direcao * clima_service.wind_speed * 0.35

            self.vento += influencia_clima * 4.0

        # Garante uma brisa mínima perceptível sem afetar ventos médios e fortes.
        MIN_VENTO_VISUAL = 0.12
        if abs(self.vento) < MIN_VENTO_VISUAL:
            self.vento = MIN_VENTO_VISUAL if self.vento >= 0 else -MIN_VENTO_VISUAL

    def eh_dia(self):
        """Retorna True se for horário comercial/dia (6h às 19h)."""
        hora_atual = datetime.now().hour
        return not (hora_atual >= 19 or hora_atual < 6)

    def esta_chovendo(self, clima_service):
        """Retorna True se o nível de nuvens for suficiente para chuva."""
        if not clima_service:
            return False
        return clima_service.cloudiness >= 70

    def obter_hora_decimal(self):
        """Retorna a hora atual em formato decimal (ex: 14.5 para 14:30)."""
        agora = datetime.now()
        return agora.hour + (agora.minute / 60)
