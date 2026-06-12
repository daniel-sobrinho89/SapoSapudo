import random


class IASapo:

    def __init__(self):

        self.cooldown = random.uniform(
            30,
            60
        )

    def obter_acao(
        self,
        dt,
        sapo
    ):

        self.cooldown -= dt

        if self.cooldown > 0:
            return None

        a = sapo.animacoes

        # =================================
        # SONHOS / EXISTENCIAIS
        # =================================

        if a.dormindo:

            self.cooldown = random.uniform(
                300,
                600
            )

            if random.random() < 0.40:
                return "existencial"

            return None

        if a.adormecendo:
            return None

        if a.acordando:
            return None

        if a.andando_esquerda:
            return None

        # =================================
        # VIOLÃO
        # =================================

        if a.tocando_violao:

            # pensa mais frequentemente
            self.cooldown = random.uniform(
                60,
                120
            )

            return random.choice([
                "violao",
                "violao",
                "violao",
                "existencial"
            ])

        # =================================
        # PADRÃO
        # =================================

        self.cooldown = random.uniform(
            120,
            300
        )

        # =================================
        # EXISTENCIAIS RAROS
        # =================================

        if random.random() < 0.02:
            return "existencial"

        # =================================
        # CLIMA
        # =================================

        clima = sapo.clima

        if clima:

            opcoes = []

            if clima.wind_speed > 30:
                opcoes.append(
                    "vento_forte"
                )

            if (
                clima.cloudiness > 90
                and clima.humidity > 85
            ):
                opcoes.append(
                    "chuva"
                )

            if clima.cloudiness > 80:
                opcoes.append(
                    "nublado"
                )

            if clima.temperature >= 32:
                opcoes.append(
                    "calor"
                )

            if clima.temperature <= 12:
                opcoes.append(
                    "frio"
                )

            if clima.humidity > 90:
                opcoes.append(
                    "umidade"
                )

            if (
                clima.future_cloudiness_1h
                > clima.cloudiness + 20
            ):
                opcoes.append(
                    "chuva_chegando"
                )

            if (
                clima.future_cloudiness_1h
                < clima.cloudiness - 20
            ):
                opcoes.append(
                    "abrindo_tempo"
                )

            if opcoes:
                return random.choice(
                    opcoes
                )

            if clima.is_day:

                return random.choice([
                    "sol",
                    "aleatorio"
                ])

            return random.choice([
                "noite",
                "aleatorio"
            ])

        return "aleatorio"