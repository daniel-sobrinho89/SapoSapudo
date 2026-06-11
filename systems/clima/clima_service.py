# ==========================================
# clima_service.py
# ==========================================

import json
import os

import requests
import random
from datetime import datetime, timedelta
from time import sleep
from utils.paths import BASE_DIR

class ClimaService:

    def __init__(self):

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

        # RAJADA (gust) global: timer e estado
        self.timer_rajada_vento = random.uniform(
            15,
            30
        )

        self.rajada_ativa = False
        self.rajada_tempo_restante = 0.0

        self.cache_file = str(BASE_DIR / "data" / "clima_cache.json")

        with open(
            str(BASE_DIR / "data" / "config.json"),
            "r",
            encoding="utf-8"
        ) as arquivo:

            CONFIG = json.load(arquivo)

        self.api_key = (
            CONFIG["weatherapi"]["api_key"]
        )

        self.proxima_tentativa = None
        
        self.hora_bloqueada = None

        self.retry_atual = 0

        self.tentativas = [
            {"segundos": 10},
            {"minutos": 2},
            {"minutos": 5},
            {"minutos": 6}
        ]

        self.carregar_cache()

        self.cloudiness_visual = self.cloudiness

    # ==========================================
    # PRECISA ATUALIZAR?
    # ==========================================

    def precisa_atualizar(self):

        agora = datetime.now()

        if self.atualizando:
            return False

        if (
            self.proxima_tentativa is not None
            and agora < self.proxima_tentativa
        ):
            return False

        if self.hora_bloqueada == agora.hour:
            return False

        return (
            agora.hour
            != self.ultima_hora_atualizada
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

        # atualizar lógica de rajada (gust)
        self.timer_rajada_vento -= dt

        if self.timer_rajada_vento <= 0 and not self.rajada_ativa:

            # iniciar rajada global
            self.rajada_ativa = True
            self.rajada_tempo_restante = random.uniform(
                3,
                8
            )

            # preparar próximo ciclo de rajadas
            self.timer_rajada_vento = random.uniform(
                180,
                300
            )

        if self.rajada_ativa:

            self.rajada_tempo_restante -= dt

            if self.rajada_tempo_restante <= 0:
                self.rajada_ativa = False
                self.rajada_tempo_restante = 0.0

    # ==========================================
    # BUSCAR CLIMA
    # ==========================================
    def consultar_weatherapi(self):

        if self.atualizando:
            return

        self.atualizando = True

        try:

            url = (
                "https://api.weatherapi.com/v1/forecast.json"
                f"?key={self.api_key}"
                "&q=auto:ip"
                "&days=2"
            )

            response = requests.get(
                url,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            if "error" in data:

                raise Exception(
                    data["error"]["message"]
                )

            # ==========================================
            # CLIMA ATUAL
            # ==========================================

            self.cloudiness = (
                data["current"]["cloud"]
            )

            self.wind_speed = (
                data["current"]["wind_kph"]
            )

            self.wind_direction = (
                data["current"]["wind_degree"]
            )

            self.is_day = (
                data["current"]["is_day"]
            )

            self.condition_code = (
                data["current"]["condition"]["code"]
            )

            self.condition_text = (
                data["current"]["condition"]["text"]
            )

            self.temperature = (
                data["current"]["temp_c"]
            )

            self.humidity = (
                data["current"]["humidity"]
            )

            # ==========================================
            # PREVISÃO HORÁRIA
            # ==========================================

            horas = (
                data["forecast"]["forecastday"][0]["hour"]
                + data["forecast"]["forecastday"][1]["hour"]
            )

            hora_local = datetime.strptime(
                data["location"]["localtime"],
                "%Y-%m-%d %H:%M"
            ).hour

            self.future_cloudiness_1h = horas[
                hora_local + 1
            ]["cloud"]

            self.future_cloudiness_2h = horas[
                hora_local + 2
            ]["cloud"]

            self.future_cloudiness_3h = horas[
                hora_local + 3
            ]["cloud"]

            # ==========================================
            # LOCALIZAÇÃO
            # ==========================================

            self.latitude = (
                data["location"]["lat"]
            )

            self.longitude = (
                data["location"]["lon"]
            )

            # ==========================================
            # CONTROLE
            # ==========================================

            self.ultima_hora_atualizada = datetime.now().hour

            self.salvar_cache()

            self.retry_atual = 0

            self.proxima_tentativa = None

            self.hora_bloqueada = None

            self.clima_disponivel = True

            # ==========================================
            # LOG
            # ==========================================

            print(
                "[CLIMA]",
                "Atual:", self.cloudiness,
                "| +1h:", self.future_cloudiness_1h,
                "| +2h:", self.future_cloudiness_2h,
                "| +3h:", self.future_cloudiness_3h,
                "| vento:", self.wind_speed,
                "| direção:", self.wind_direction,
                "| Temperatura:", self.temperature,
                "| Umidade:", self.humidity
            )

        finally:

            self.atualizando = False

    def atualizar(self):
        self.clima_disponivel = False

        try:

            self.consultar_weatherapi()

            self.clima_disponivel = True

        except Exception as ex:

            print(
                "[CLIMA] Falha:",
                ex
            )

            self.retry_atual += 1

            if self.retry_atual <= len(self.tentativas):

                tentativa = self.tentativas[
                    self.retry_atual - 1
                ]

                if "segundos" in tentativa:

                    self.proxima_tentativa = (
                        datetime.now()
                        + timedelta(
                            seconds=tentativa["segundos"]
                        )
                    )

                    print(
                        f"[CLIMA] Nova tentativa em "
                        f"{tentativa['segundos']} segundos"
                    )

                else:

                    self.proxima_tentativa = (
                        datetime.now()
                        + timedelta(
                            minutes=tentativa["minutos"]
                        )
                    )

                    print(
                        f"[CLIMA] Nova tentativa em "
                        f"{tentativa['minutos']} minutos"
                    )

            else:

                self.hora_bloqueada = (
                    datetime.now().hour
                )

                self.proxima_tentativa = None

                print(
                    "[CLIMA] Todas as tentativas falharam. "
                    "Nova tentativa somente na próxima hora."
                )



    def carregar_cache(self):

        if not os.path.exists(
            self.cache_file
        ):
            return

        try:

            with open(
                self.cache_file,
                "r",
                encoding="utf-8"
            ) as arquivo:

                data = json.load(
                    arquivo
                )

            self.cloudiness = data.get(
                "cloudiness",
                0
            )

            self.wind_speed = data.get(
                "wind_speed",
                0
            )

            self.wind_direction = data.get(
                "wind_direction",
                0
            )

            self.temperature = data.get(
                "temperature",
                0
            )

            self.humidity = data.get(
                "humidity",
                0
            )

            self.future_cloudiness_1h = data.get(
                "future_cloudiness_1h",
                self.cloudiness
            )

            self.future_cloudiness_2h = data.get(
                "future_cloudiness_2h",
                self.cloudiness
            )

            self.future_cloudiness_3h = data.get(
                "future_cloudiness_3h",
                self.cloudiness
            )

            self.is_day = data.get(
                "is_day",
                1
            )

            self.condition_code = data.get(
                "condition_code",
                1000
            )

            self.condition_text = data.get(
                "condition_text",
                "Clear"
            )

            print(
                "[CLIMA] Cache carregado."
            )

        except Exception as ex:

            print(
                "[CLIMA] Erro carregando cache:",
                ex
            )

    def salvar_cache(self):

        try:

            os.makedirs(
                str(BASE_DIR / "data"),
                exist_ok=True
            )

            with open(
                self.cache_file,
                "w",
                encoding="utf-8"
            ) as arquivo:

                json.dump(
                    {
                        "cloudiness": self.cloudiness,
                        "wind_speed": self.wind_speed,
                        "wind_direction": self.wind_direction,
                        "future_cloudiness_1h": self.future_cloudiness_1h,
                        "future_cloudiness_2h": self.future_cloudiness_2h,
                        "future_cloudiness_3h": self.future_cloudiness_3h,
                        "is_day": self.is_day,
                        "condition_code": self.condition_code,
                        "condition_text": self.condition_text,
                        "temperature": self.temperature,
                        "humidity": self.humidity
                    },
                    arquivo,
                    indent=4
                )

        except Exception as ex:

            print(
                "[CLIMA] Erro salvando cache:",
                ex
            )