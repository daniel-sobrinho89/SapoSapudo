import random
import math


def atualizar_piscada(semente, dt):

    semente.timer_piscada -= dt

    if not semente.piscando:

        if semente.timer_piscada <= 0:

            semente.piscando = True

            semente.tempo_piscando = (
                semente.duracao_piscada
            )

    else:

        semente.tempo_piscando -= dt

        if semente.tempo_piscando <= 0:

            semente.piscando = False

            semente.timer_piscada = (
                random.uniform(
                    2,
                    5
                )
            )


def aplicar_vento(semente, clima_service, dt):


    velocidade_vento = (
        clima_service.wind_speed
    )

    semente.sorrindo = True

    # Se houver uma rajada global do clima, iniciar flutuação na semente
    if clima_service.rajada_ativa and semente.tempo_flutuando <= 0:

        semente.tempo_flutuando = random.uniform(
            3,
            8
        )

        semente.sustentacao_restante = 1.0

        semente.altura_alvo_flutuacao = (
            random.uniform(
                180,
                350
            )
        )

        semente.entrar_flutuando()

    if semente.tempo_flutuando > 0:

        semente.tempo_flutuando -= dt

        semente.sustentacao_restante = 1.0

        semente.entrar_flutuando()

    else:

        semente.sustentacao_restante -= (
            dt * 0.50
        )

        semente.sustentacao_restante = max(
            0,
            semente.sustentacao_restante
        )

        semente.flutuando = (
            semente.sustentacao_restante > 0
        )

        if not semente.flutuando:

            if semente.estava_flutuando:

                semente.marcar_pousando_do_vento()

            semente.offset_flutuacao_x *= 0.50
            semente.offset_flutuacao_y *= 0.50

            return

    semente.flutuando = True
    semente.sorrindo = False

    direcao = (
        clima_service.wind_direction
    )

    rad = math.radians(
        direcao + 180
    )

    intensidade = min(
        velocidade_vento,
        40
    )

    semente.fase_flutuacao += (
        dt * 2.0
    )

    semente.offset_flutuacao_x = (
        math.sin(
            semente.fase_flutuacao
        )
        * 25
    )

    semente.offset_flutuacao_y = (
        math.sin(
            semente.fase_flutuacao * 1.7
        )
        * 12
    )

    semente.vel_x += (
        math.sin(rad)
        * intensidade
        * 0.08
    )

    semente.vel_x = max(
        -80,
        min(
            80,
            semente.vel_x
        )
    )

    erro = (
        semente.altura_alvo_flutuacao
        - semente.y
    )

    semente.vel_y += (
        erro
        * 0.015
        * semente.sustentacao_restante
    )

    semente.estava_flutuando = True
