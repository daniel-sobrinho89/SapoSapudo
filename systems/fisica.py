import math


class SistemaFisica:

    def aplicar_gravidade(self, entidade, dt):
        gravidade = (
            entidade.gravidade
            * (
                1
                - (
                    entidade.sustentacao_restante
                    * 0.80
                )
            )
        )

        entidade.vel_y += (
            gravidade * dt
        )

    def aplicar_gravidade_simples(
        self,
        entidade,
        dt,
        intensidade=4.0
    ):

        entidade.vel_y += (
            intensidade * dt
        )

    def integrar_movimento(self, entidade, dt):
        entidade.x += (
            entidade.vel_x * dt
        )

        entidade.y += (
            entidade.vel_y * dt
        )

    def resolver_limites(self, entidade, clima_service):
        altura_maxima = (
            entidade.limite_chao
            - (
                clima_service.wind_speed * 8
            )
        )

        altura_maxima = max(
            120,
            altura_maxima
        )

        if entidade.y < altura_maxima:

            entidade.y = altura_maxima

            if entidade.vel_y < 0:
                entidade.vel_y = 0

        if entidade.no_chao:

            entidade.vel_x *= 0.3

            if abs(entidade.vel_x) < 2:
                entidade.vel_x = 0

        else:

            entidade.vel_x *= 0.99

        if entidade.y >= entidade.limite_chao:

            pousou_agora = (
                not entidade.no_chao
            )

            entidade.y = entidade.limite_chao

            entidade.vel_y = 0
            entidade.vel_x = 0

            entidade.offset_flutuacao_x = 0
            entidade.offset_flutuacao_y = 0

            entidade.flutuando = False

            entidade.no_chao = True

            # Delegar ação de pouso para a entidade (método em português)
            if hasattr(entidade, 'ao_pousar'):
                entidade.ao_pousar(pousou_agora)
            elif hasattr(entidade, 'on_land'):
                entidade.on_land(pousou_agora)

        else:

            entidade.no_chao = False

    def aplicar_forca_vento(self, entidade, clima_service=None, dt=0, sensibilidade=1.0, vento_speed=None, vento_direction=None):
        """Aplica uma força horizontal simples causada pelo vento.

        Parâmetros aceitos:
        - clima_service: objeto com `wind_speed` e `wind_direction` (opcional)
        - vento_speed / vento_direction: valores explícitos que têm prioridade
        - sensibilidade: multiplicador por entidade
        """
        # prioridade para valores explícitos
        if vento_speed is not None:
            velocidade_vento = vento_speed
        elif clima_service is not None:
            velocidade_vento = getattr(clima_service, 'wind_speed', 0)
        else:
            velocidade_vento = getattr(entidade, 'wind_speed', 0)

        if vento_direction is not None:
            direcao = vento_direction
        elif clima_service is not None:
            direcao = getattr(clima_service, 'wind_direction', 0)
        else:
            direcao = getattr(entidade, 'wind_direction', 0)

        # fator base que pode ser modificado pela entidade
        afinidade = getattr(entidade, 'wind_affinity', sensibilidade)

        rad = math.radians(direcao + 180)

        intensidade = min(velocidade_vento, 40) * afinidade

        delta_v = math.sin(rad) * intensidade * 0.08

        # Aplicar no atributo apropriado: vel_x, velocidade_x, vx
        if hasattr(entidade, 'vel_x'):
            entidade.vel_x += delta_v * dt
        elif hasattr(entidade, 'velocidade_x'):
            entidade.velocidade_x += delta_v * dt
        elif hasattr(entidade, 'vx'):
            entidade.vx += delta_v * dt
        else:
            # fallback genérico
            prev = getattr(entidade, 'vel_x', 0)
            setattr(entidade, 'vel_x', prev + delta_v * dt)


# Singleton do sistema de física para uso geral
sistema_fisica = SistemaFisica()
