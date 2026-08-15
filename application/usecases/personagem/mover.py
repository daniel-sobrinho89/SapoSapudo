import traceback
from math import hypot


class MoverPersonagemUseCase:
    def _atualizar_estado_animacao(self, personagem, dx, estado_normal, estado_flip):
        """Helper para definir o flip da animação dependendo da direção do movimento."""
        personagem.animacoes.estado = estado_normal if dx >= 0 else estado_flip

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

            # Se já está perto o suficiente, apenas para.
            if hypot(dx, dy) < 2:
                self._atualizar_estado_animacao(
                    personagem, dx, estado_parado, estado_parado_flip
                )
                return False

            x_antigo, y_antigo = personagem.x, personagem.y
            passo_maximo = velocidade * dt

            # Tenta mover
            nova_posicao = navegacao.limitar_movimento(
                x_antigo,
                y_antigo,
                personagem.destino_x,
                personagem.destino_y,
                personagem.altura,
                passo_maximo,
            )

            if not nova_posicao:
                personagem.destino_x, personagem.destino_y = personagem.x, personagem.y
                self._atualizar_estado_animacao(
                    personagem, dx, estado_parado, estado_parado_flip
                )
                return False

            # Atualiza altura se houver degrau/transição
            nova_altura = navegacao.obter_altura_transicao(
                x_antigo, y_antigo, nova_posicao[0], nova_posicao[1], personagem.altura
            )
            if nova_altura is not None:
                personagem.altura = nova_altura

            personagem.x, personagem.y = nova_posicao

            # Tratativa caso o personagem tenha "travado" no cenário (andou muito pouco)
            if hypot(personagem.x - x_antigo, personagem.y - y_antigo) < 1:
                novo_destino = navegacao.encontrar_desvio(
                    personagem.x,
                    personagem.y,
                    personagem.destino_x,
                    personagem.destino_y,
                    personagem.altura,
                    distancia_maxima=passo_maximo,
                )

                if novo_destino is None:
                    # Trava a posição atual e volta pro estado parado
                    personagem.destino_x, personagem.destino_y = (
                        personagem.x,
                        personagem.y,
                    )
                    self._atualizar_estado_animacao(
                        personagem, dx, estado_parado, estado_parado_flip
                    )
                    return False

                personagem.destino_x, personagem.destino_y = novo_destino
                return True

            # Movimentação ocorreu normalmente, continua correndo
            passo_x = personagem.x - x_antigo
            self._atualizar_estado_animacao(
                personagem, passo_x, estado_correndo, estado_correndo_flip
            )
            return True

        except Exception:
            traceback.print_exc()
            return False
