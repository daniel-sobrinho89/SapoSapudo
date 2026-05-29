# ==========================================
# clima_service.py
# ==========================================

import requests
from datetime import datetime


class ClimaService:

    def __init__(self):

        # São Paulo
        self.latitude = -23.55
        self.longitude = -46.63

        # clima atual
        self.cloudiness = 0
        self.cloudiness_visual = 0

        # previsão futura
        self.future_cloudiness_1h = 0
        self.future_cloudiness_2h = 0
        self.future_cloudiness_3h = 0

        # controle
        self.atualizando = False
        self.ultima_hora_atualizada = -1
        self.clima_disponivel = False

        # VENTO
        self.wind_direction = 0
        self.wind_speed = 0

    # ==========================================
    # PRECISA ATUALIZAR?
    # ==========================================

    def precisa_atualizar(self):

        hora_atual = datetime.now().hour

        return (
            hora_atual != self.ultima_hora_atualizada
            and not self.atualizando
        )
    
    # ==========================================
    # SUAVIZAÇÃO VISUAL
    # ==========================================

    def atualizar_visual(self, dt):

        velocidade = 1.5

        self.cloudiness_visual += (
            self.cloudiness
            - self.cloudiness_visual
        ) * velocidade * dt

    # ==========================================
    # BUSCAR CLIMA
    # ==========================================

    def atualizar(self):

        if self.atualizando:
            return

        self.atualizando = True

        try:

            url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={self.latitude}"
                f"&longitude={self.longitude}"
                "&hourly=cloud_cover,wind_direction_10m,wind_speed_10m"
                "&forecast_days=2"
                "&timezone=auto"
            )

            response = requests.get(
                url,
                timeout=5
            )

            data = response.json()

            horas = data["hourly"]["time"]
            nuvens = data["hourly"]["cloud_cover"]
            direcoes = data["hourly"]["wind_direction_10m"]
            velocidades = data["hourly"]["wind_speed_10m"]

            agora = datetime.now()

            indice_atual = 0

            for i, hora in enumerate(horas):

                hora_dt = datetime.fromisoformat(hora)

                if (
                    hora_dt.year == agora.year
                    and hora_dt.month == agora.month
                    and hora_dt.day == agora.day
                    and hora_dt.hour == agora.hour
                ):

                    indice_atual = i
                    break

            # clima atual
            self.cloudiness = nuvens[indice_atual]
            self.wind_direction = direcoes[indice_atual]
            self.wind_speed = velocidades[indice_atual]

            # previsões
            self.future_cloudiness_1h = nuvens[
                min(indice_atual + 1, len(nuvens) - 1)
            ]

            self.future_cloudiness_2h = nuvens[
                min(indice_atual + 2, len(nuvens) - 1)
            ]

            self.future_cloudiness_3h = nuvens[
                min(indice_atual + 3, len(nuvens) - 1)
            ]

            # salva hora atualizada SOMENTE em sucesso
            self.ultima_hora_atualizada = agora.hour
            
            self.clima_disponivel = True

            print(
                "[CLIMA]",
                "Atual:", self.cloudiness,
                "| +1h:", self.future_cloudiness_1h,
                "| +2h:", self.future_cloudiness_2h,
                "| +3h:", self.future_cloudiness_3h
            )

        except Exception as e:

            self.clima_disponivel = False

            print(f"[CLIMA] Falha ao consultar API: {e}")

        finally:

            self.atualizando = False