import traceback
from math import hypot


class MoverPersonagemUseCase:
    # Rotas de desvio são calculadas uma vez por destino e seguidas por
    # waypoints. Isso evita um BFS novo a cada frame quando uma construção
    # bloqueia o caminho para uma árvore/mina.
    DISTANCIA_WAYPOINT = 4.0

    def __init__(self):
        self._rotas_por_personagem = {}

    def _atualizar_estado_animacao(self, personagem, dx, estado_normal, estado_flip):
        personagem.animacoes.estado = estado_normal if dx >= 0 else estado_flip

    def _limpar_rota(self, personagem):
        self._rotas_por_personagem.pop(id(personagem), None)

    def _criar_rota(self, personagem, navegacao, alvo_original):
        try:
            rota = navegacao.calcular_rota(
                personagem.x,
                personagem.y,
                alvo_original[0],
                alvo_original[1],
                personagem.altura,
            )
        except Exception:
            traceback.print_exc()
            return False

        if not rota:
            return False

        self._rotas_por_personagem[id(personagem)] = {
            "alvo": alvo_original,
            "rota": rota,
            "indice": 0,
            "versao_obstaculos": getattr(navegacao, "_versao_obstaculos", None),
        }
        return True

    def _preparar_waypoint(self, personagem, navegacao):
        dados = self._rotas_por_personagem.get(id(personagem))
        if not dados:
            return False

        if dados["versao_obstaculos"] != getattr(navegacao, "_versao_obstaculos", None):
            self._limpar_rota(personagem)
            return False

        rota = dados["rota"]
        indice = dados["indice"]

        while (
            indice < len(rota)
            and hypot(
                rota[indice][0] - personagem.x,
                rota[indice][1] - personagem.y,
            )
            <= self.DISTANCIA_WAYPOINT
        ):
            indice += 1

        dados["indice"] = indice

        if indice >= len(rota):
            alvo = dados["alvo"]
            self._limpar_rota(personagem)
            personagem.destino_x, personagem.destino_y = alvo
            return False

        personagem.destino_x, personagem.destino_y = rota[indice]
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
            destino_recebido = (personagem.destino_x, personagem.destino_y)
            dados = self._rotas_por_personagem.get(id(personagem))

            # Se havia uma rota, destino_x/destino_y normalmente apontam para
            # o waypoint criado por este próprio movimentador. Só descarte a
            # rota quando o chamador realmente mudou para outro destino.
            if dados is not None:
                rota = dados["rota"]
                indice = dados["indice"]
                esperado = dados["alvo"]
                if indice < len(rota):
                    esperado = rota[indice]

                if (
                    hypot(
                        destino_recebido[0] - esperado[0],
                        destino_recebido[1] - esperado[1],
                    )
                    > 8
                ):
                    self._limpar_rota(personagem)
                    dados = None

            if dados is not None and not self._preparar_waypoint(personagem, navegacao):
                dados = self._rotas_por_personagem.get(id(personagem))

            if dados is not None:
                alvo = (personagem.destino_x, personagem.destino_y)
            else:
                alvo = destino_recebido

            dx = alvo[0] - personagem.x
            dy = alvo[1] - personagem.y

            if hypot(dx, dy) < 2:
                self._limpar_rota(personagem)
                self._atualizar_estado_animacao(
                    personagem, dx, estado_parado, estado_parado_flip
                )
                return False

            x_antigo, y_antigo = personagem.x, personagem.y
            passo_maximo = velocidade * dt

            if dados is not None:
                nova_posicao = navegacao._limitar_distancia(
                    x_antigo,
                    y_antigo,
                    alvo[0],
                    alvo[1],
                    passo_maximo,
                )
            else:
                nova_posicao = navegacao.limitar_movimento(
                    x_antigo,
                    y_antigo,
                    alvo[0],
                    alvo[1],
                    personagem.altura,
                    passo_maximo,
                )

                if nova_posicao is None and self._criar_rota(
                    personagem, navegacao, destino_recebido
                ):
                    self._preparar_waypoint(personagem, navegacao)
                    nova_posicao = navegacao._limitar_distancia(
                        x_antigo,
                        y_antigo,
                        personagem.destino_x,
                        personagem.destino_y,
                        passo_maximo,
                    )

            if not nova_posicao:
                self._limpar_rota(personagem)
                personagem.destino_x, personagem.destino_y = (
                    personagem.x,
                    personagem.y,
                )
                self._atualizar_estado_animacao(
                    personagem, dx, estado_parado, estado_parado_flip
                )
                return False

            nova_altura = navegacao.obter_altura_transicao(
                x_antigo,
                y_antigo,
                nova_posicao[0],
                nova_posicao[1],
                personagem.altura,
            )
            if nova_altura is not None:
                personagem.altura = nova_altura

            personagem.x, personagem.y = nova_posicao

            # Ao alcançar um waypoint, prepara o próximo na próxima chamada.
            # Não recalcula a rota inteira.
            dados = self._rotas_por_personagem.get(id(personagem))
            if dados is not None:
                while (
                    dados["indice"] < len(dados["rota"])
                    and hypot(
                        dados["rota"][dados["indice"]][0] - personagem.x,
                        dados["rota"][dados["indice"]][1] - personagem.y,
                    )
                    <= self.DISTANCIA_WAYPOINT
                ):
                    dados["indice"] += 1

                if dados["indice"] >= len(dados["rota"]):
                    alvo_final = dados["alvo"]
                    self._limpar_rota(personagem)
                    personagem.destino_x, personagem.destino_y = alvo_final

            passo_x = personagem.x - x_antigo
            self._atualizar_estado_animacao(
                personagem, passo_x, estado_correndo, estado_correndo_flip
            )
            return True

        except Exception:
            traceback.print_exc()
            return False
