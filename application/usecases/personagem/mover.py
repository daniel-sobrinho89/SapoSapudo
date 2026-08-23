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

    def notificar_obstaculos_alterados(self, navegacao):
        versao = getattr(navegacao, "_versao_obstaculos", None)
        removidas = 0
        for _chave, dados in list(self._rotas_por_personagem.items()):
            if versao is not None:
                dados["versao_pendente"] = versao
        return removidas

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
        destino_externo=None,
    ):
        try:
            destino_recebido = (personagem.destino_x, personagem.destino_y)
            dados = self._rotas_por_personagem.get(id(personagem))
            destino_final = (
                destino_externo
                if destino_externo is not None
                else (dados["alvo"] if dados is not None else destino_recebido)
            )

            # Ações como combate atualizam destino_x/destino_y continuamente
            # para representar o ponto de ataque. Isso não pode ser confundido
            # com uma nova ordem e destruir o waypoint persistente a cada frame.
            # Quando existe um destino externo, comparamos somente esse destino
            # final com a rota atual.
            if dados is not None:
                if destino_externo is not None:
                    if (
                        hypot(
                            destino_externo[0] - dados["alvo"][0],
                            destino_externo[1] - dados["alvo"][1],
                        )
                        > 12
                    ):
                        self._limpar_rota(personagem)
                        dados = None
                        destino_final = destino_externo
                else:
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

            if dados is not None:
                versao_atual = getattr(navegacao, "_versao_obstaculos", None)
                if dados["versao_obstaculos"] != versao_atual:
                    rota_afetada = navegacao.rota_foi_afetada(
                        dados["rota"],
                        dados["indice"],
                        dados["versao_obstaculos"],
                        origem=(personagem.x, personagem.y),
                    )
                    if rota_afetada:
                        destino_final = dados["alvo"]
                        self._limpar_rota(personagem)
                        dados = None
                    else:
                        # A construção/obstáculo mudou fora do trecho restante.
                        # A rota continua válida, apenas atualizamos sua versão.
                        dados["versao_obstaculos"] = versao_atual
                        dados.pop("versao_pendente", None)

                if dados is not None and not self._preparar_waypoint(
                    personagem, navegacao
                ):
                    dados = self._rotas_por_personagem.get(id(personagem))

            if dados is not None:
                alvo = (personagem.destino_x, personagem.destino_y)
            else:
                alvo = destino_final

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
                caminho_livre = navegacao._caminho_livre(
                    x_antigo,
                    y_antigo,
                    alvo[0],
                    alvo[1],
                    personagem.altura,
                )

                if caminho_livre and navegacao.pode_andar(
                    alvo[0], alvo[1], personagem.altura
                ):
                    nova_posicao = navegacao._limitar_distancia(
                        x_antigo,
                        y_antigo,
                        alvo[0],
                        alvo[1],
                        passo_maximo,
                    )
                else:
                    # A partir do primeiro bloqueio, cria uma rota persistente
                    # e passa a consumir seus waypoints. Não pede BFS novamente
                    # a cada frame enquanto o obstáculo permanecer igual.
                    nova_posicao = None
                    if self._criar_rota(personagem, navegacao, destino_final):
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
                else:
                    # O waypoint foi consumido neste frame. Atualiza já o
                    # destino exposto ao restante do jogo para que o próximo
                    # frame não interprete a troca legítima de waypoint como
                    # uma nova ordem manual.
                    personagem.destino_x, personagem.destino_y = dados["rota"][
                        dados["indice"]
                    ]

            passo_x = personagem.x - x_antigo
            self._atualizar_estado_animacao(
                personagem, passo_x, estado_correndo, estado_correndo_flip
            )
            return True

        except Exception:
            traceback.print_exc()
            return False
