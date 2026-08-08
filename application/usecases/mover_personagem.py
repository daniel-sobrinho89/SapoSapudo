import traceback
from math import hypot


class MoverPersonagemUseCase:
    def ir_para(
        self,
        personagem,
        navegacao,
        destino_x,
        destino_y,
        velocidade,
        dt,
    ):
        posicao = navegacao.limitar_movimento(
            personagem.x,
            personagem.y,
            destino_x,
            destino_y,
            personagem.altura,
            distancia_maxima=velocidade * dt,
        )

        if posicao is None:
            return False

        personagem.x, personagem.y = posicao

        return True

    def executar(
        self,
        personagem,
        navegacao,
        velocidade,
        estado_correndo,
        estado_correndo_flip,
        estado_parado,
        estado_parado_flip,
        dt,
    ):
        try:
            dx = personagem.destino_x - personagem.x
            dy = personagem.destino_y - personagem.y

            distancia = hypot(dx, dy)

            if distancia < 2:
                if dx >= 0:
                    personagem.animacoes.estado = estado_parado
                else:
                    personagem.animacoes.estado = estado_parado_flip

                return False

            x_antigo = personagem.x
            y_antigo = personagem.y

            alvo_x, alvo_y = personagem.destino_x, personagem.destino_y

            if not navegacao.pode_andar(alvo_x, alvo_y, personagem.altura):
                alvo_x, alvo_y = navegacao.ajustar_posicao(
                    alvo_x, alvo_y, personagem.altura
                ) or (
                    personagem.x,
                    personagem.y,
                )

            nova_posicao = navegacao.limitar_movimento(
                personagem.x,
                personagem.y,
                alvo_x,
                alvo_y,
                personagem.altura,
                velocidade * dt,
            )

            if nova_posicao is None:
                return False

            nova_posicao = navegacao.ajustar_posicao(
                nova_posicao[0],
                nova_posicao[1],
                personagem.altura,
            ) or (
                personagem.x,
                personagem.y,
            )

            personagem.x, personagem.y = nova_posicao

            deslocamento = hypot(
                personagem.x - x_antigo,
                personagem.y - y_antigo,
            )

            if deslocamento < 1:
                novo_destino = navegacao.encontrar_desvio(
                    personagem.x,
                    personagem.y,
                    personagem.destino_x,
                    personagem.destino_y,
                    personagem.altura,
                    distancia_maxima=velocidade * dt,
                )

                if novo_destino is None:
                    personagem.destino_x = personagem.x
                    personagem.destino_y = personagem.y

                    if dx >= 0:
                        personagem.animacoes.estado = estado_parado
                    else:
                        personagem.animacoes.estado = estado_parado_flip

                    return False

                personagem.destino_x, personagem.destino_y = novo_destino

                return True

            if dx >= 0:
                personagem.animacoes.estado = estado_correndo
            else:
                personagem.animacoes.estado = estado_correndo_flip

            return True
        except Exception:
            traceback.print_exc()

            return False
