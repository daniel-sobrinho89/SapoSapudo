import traceback
from math import hypot


class MoverPersonagemUseCase:
    # Rotas de desvio são calculadas uma vez por destino e seguidas por
    # waypoints. Isso evita um BFS novo a cada frame quando uma construção
    # bloqueia o caminho para uma árvore/mina.
    DISTANCIA_WAYPOINT = 4.0

    def __init__(self):
        self._rotas_por_personagem = {}

    def _atualizar_estado_animacao(
        self,
        personagem,
        dx,
        estado_normal=None,
        estado_flip=None,
        nome_animacao=None,
    ):
        """Atualiza a apresentação sem tornar o movimento dependente do domínio.

        Os parâmetros de estado antigos permanecem aceitos para compatibilidade
        durante a migração. Novos chamadores podem informar apenas
        ``nome_animacao``.
        """
        animacoes = getattr(personagem, "animacoes", None)
        if animacoes is None:
            return

        if hasattr(animacoes, "flip_para_direcao"):
            flip = animacoes.flip_para_direcao(dx)
        else:
            flip = dx < 0

        if nome_animacao is not None and hasattr(animacoes, "definir"):
            animacoes.definir(nome_animacao, flip=flip)
            return

        if estado_normal is not None and estado_flip is not None:
            animacoes.definir(estado_flip if flip else estado_normal)

    def _limpar_rota(self, personagem):
        self._rotas_por_personagem.pop(id(personagem), None)

    def cancelar_rota(self, personagem):
        """Cancela explicitamente qualquer rota persistente do personagem."""
        self._limpar_rota(personagem)
        if personagem is not None:
            personagem.destino_x = personagem.x
            personagem.destino_y = personagem.y

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
        estado_correndo=None,
        estado_correndo_flip=None,
        estado_parado=None,
        estado_parado_flip=None,
        dt=0.0,
        destino_externo=None,
        animacao_correndo=None,
        animacao_parado=None,
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
                    personagem,
                    dx,
                    estado_parado,
                    estado_parado_flip,
                    nome_animacao=animacao_parado,
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
                    personagem,
                    dx,
                    estado_parado,
                    estado_parado_flip,
                    nome_animacao=animacao_parado,
                )
                return False

            # Uma posição calculada igual à posição atual não é movimento.
            # Não deixe o personagem permanecer em "correndo" quando a
            # navegação encontrou um trecho sem progresso real.
            deslocamento_calculado = hypot(
                nova_posicao[0] - x_antigo,
                nova_posicao[1] - y_antigo,
            )
            if deslocamento_calculado <= 0.0001:
                self._limpar_rota(personagem)
                personagem.destino_x, personagem.destino_y = (
                    personagem.x,
                    personagem.y,
                )
                self._atualizar_estado_animacao(
                    personagem,
                    0.0,
                    estado_parado,
                    estado_parado_flip,
                    nome_animacao=animacao_parado,
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

            # Se este foi o último trecho e chegamos efetivamente ao destino,
            # encerra a corrida neste mesmo frame. Isso evita um frame (ou,
            # em rotas inválidas, vários frames) de "correndo" parado.
            dados_apos_movimento = self._rotas_por_personagem.get(id(personagem))
            alvo_atual = (
                (personagem.destino_x, personagem.destino_y)
                if dados_apos_movimento is None
                else (personagem.destino_x, personagem.destino_y)
            )
            if (
                dados_apos_movimento is None
                and hypot(
                    alvo_atual[0] - personagem.x,
                    alvo_atual[1] - personagem.y,
                )
                <= 2.0
            ):
                self._atualizar_estado_animacao(
                    personagem,
                    personagem.x - x_antigo,
                    estado_parado,
                    estado_parado_flip,
                    nome_animacao=animacao_parado,
                )
                return True

            passo_x = personagem.x - x_antigo
            orientacao_x = passo_x
            if abs(orientacao_x) < 0.0001:
                # Em trechos verticais não use o alvo final para decidir a
                # orientação. O alvo pode estar do outro lado de um barranco,
                # fazendo a unidade parecer andar de costas. Mantemos a última
                # orientação horizontal enquanto não houver deslocamento em X.
                orientacao_x = 0.0
            self._atualizar_estado_animacao(
                personagem,
                orientacao_x,
                estado_correndo,
                estado_correndo_flip,
                nome_animacao=animacao_correndo,
            )
            return True

        except Exception:
            traceback.print_exc()
            return False
