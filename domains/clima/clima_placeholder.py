# domains/clima/clima_placeholder.py


class ClimaPlaceholder:
    temperature = 25

    cloudiness = 0
    cloudiness_visual = 0

    future_cloudiness_1h = 0
    future_cloudiness_2h = 0
    future_cloudiness_3h = 0

    wind_direction = 0
    wind_speed = 0

    rajada_ativa = False

    def __getattr__(self, name):
        return 0

    def precisa_atualizar(self):
        return False

    def atualizar_visual(self, dt):
        pass
