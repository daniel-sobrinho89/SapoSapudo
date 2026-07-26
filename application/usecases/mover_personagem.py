import traceback
from math import hypot


class MoverPersonagemUseCase:
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

            novo_x = personagem.x + dx / distancia * velocidade * dt
            novo_y = personagem.y + dy / distancia * velocidade * dt

            personagem.x, personagem.y = navegacao.limitar_movimento(
                personagem.x,
                personagem.y,
                novo_x,
                novo_y,
            )

            if dx >= 0:
                personagem.animacoes.estado = estado_correndo
            else:
                personagem.animacoes.estado = estado_correndo_flip

            return True
        except Exception:
            traceback.print_exc()

            return False
