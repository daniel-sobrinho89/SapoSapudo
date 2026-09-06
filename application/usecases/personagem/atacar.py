from math import hypot

from application.usecases.personagem.chamar_defensores import (
    ChamarDefensoresUseCase,
)
from core.game_config import obter_config
from utils.config import TILE_SIZE


class AtacarPersonagemUseCase:
    VELOCIDADE = 110
    # Espaço de combate: a unidade para um pouco antes do corpo do alvo,
    # evitando que os sprites se encostem durante o ataque.
    DISTANCIA_PARADA = 54
    DISTANCIA_DESLOCAMENTO_PARA_PERSEGUIR = 40
    DISTANCIA_LATERAL_ATAQUE = 40
    DISTANCIA_ATAQUE_CONSTRUCAO = 10
    DISTANCIA_PARADA_CONSTRUCAO = 2
    TEMPO_MINIMO_ATAQUE = 0.25
    RAIO_DETECCAO_INIMIGO_EM_TILES = 4
    RAIO_DETECCAO_INIMIGO = RAIO_DETECCAO_INIMIGO_EM_TILES * TILE_SIZE

    _sequencia_ataques = 0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.navegacao = cenario_principal.navegacao
        self.entidade_alvo = None
        self.personagem = None

        self.tempo = 0.0
        self.flip = False
        self.posicao_alvo_no_inicio_ataque = None
        self.destino_ataque = None
        self.posicao_alvo_destino_ataque = None
        self.ordem_ataque = None
        self.atacantes_recebidos = {}
        self.destino_ataque = None
        self.posicao_alvo_destino_ataque = None
        self.chamar_defensores = ChamarDefensoresUseCase(cenario_principal)
        self.busca_automatica_bloqueada = False

    @classmethod
    def _proxima_ordem_ataque(cls):
        cls._sequencia_ataques += 1
        return cls._sequencia_ataques

    def _registrar_alvo_ativo(self, alvo):
        if alvo is None or alvo is self.personagem:
            return
        registrar = getattr(self.cenario_principal, "registrar_atacante", None)
        if registrar is not None:
            registrar(alvo, self.personagem)

    def _desregistrar_alvo_ativo(self, alvo):
        if alvo is None:
            return
        remover = getattr(self.cenario_principal, "remover_atacante", None)
        if remover is not None:
            remover(alvo, self.personagem)

    def iniciar(self, personagemalvo, personagem, manual=False):
        mesmo_alvo = self.entidade_alvo is personagemalvo
        maquina_personagem = None
        estava_atacando = bool(
            maquina_personagem
            and getattr(maquina_personagem, "atacando", lambda: False)()
        )
        metodo_defendendo = getattr(maquina_personagem, "defendendo", None)
        estava_defendendo = bool(
            maquina_personagem and callable(metodo_defendendo) and metodo_defendendo()
        )

        self.personagem = personagem

        # Durante deslocamento, a orientação visual é responsabilidade do
        # movimento real. O alvo define navegação e alcance, nunca o lado para
        # o qual o sprite deve olhar enquanto ainda está se deslocando.

        if manual:
            self.atacantes_recebidos.clear()
            self.busca_automatica_bloqueada = False

        if estava_atacando and mesmo_alvo:
            self.entidade_alvo = personagemalvo
            return

        if (
            not manual
            and self.entidade_alvo is not None
            and not mesmo_alvo
            and not self._deve_trocar_alvo_ao_iniciar(personagemalvo)
        ):
            return

        self._desregistrar_alvo_ativo(self.entidade_alvo)
        self.tempo = 0.0
        self.entidade_alvo = personagemalvo
        self._registrar_alvo_ativo(self.entidade_alvo)
        self.posicao_alvo_no_inicio_ataque = None

        # O combate aceito redefine a área de movimentação livre para a
        # região do alvo. Isso vale para ordens manuais e para aquisições
        # automáticas de inimigos.
        if personagemalvo is not None:
            personagem.definir_base_movimento(
                personagemalvo.x,
                personagemalvo.y,
            )

        if not mesmo_alvo or self.ordem_ataque is None:
            self.ordem_ataque = self._proxima_ordem_ataque()

        # Uma agressão recebida pode ser confirmada pelo coordenador no
        # frame seguinte ao golpe. Se a caveira já estiver executando a
        # animação de defesa, não podemos reiniciar a movimentação aqui,
        # senão CORRENDO sobrescreve DEFENDENDO. A defesa termina sozinha e,
        # somente depois disso, o fluxo normal retoma o combate.
        if (
            not estava_atacando
            and not estava_defendendo
            and not getattr(personagem, "defesa_ativa", False)
        ):
            self._iniciar_animacao_movimento()

    def _deve_trocar_alvo_ao_iniciar(self, novo_alvo):
        alvo_atual = self.entidade_alvo

        if alvo_atual is None:
            return True

        if self._alvo_e_construcao(alvo_atual):
            return True

        if novo_alvo not in self.atacantes_recebidos:
            return True

        if not self._atacante_ainda_e_uma_ameaca(alvo_atual):
            return True

        vida_atual = getattr(alvo_atual, "vida", 0)
        vida_nova = getattr(novo_alvo, "vida", 0)

        return vida_nova < vida_atual

    def cancelar(self):
        self._desregistrar_alvo_ativo(self.entidade_alvo)
        self.entidade_alvo = None
        self.posicao_alvo_no_inicio_ataque = None
        self.destino_ataque = None
        self.posicao_alvo_destino_ataque = None
        self.ordem_ataque = None

    def bloquear_busca_automatica_ate_destino(self):
        self._desregistrar_alvo_ativo(self.entidade_alvo)
        self.entidade_alvo = None
        self.posicao_alvo_no_inicio_ataque = None
        self.destino_ataque = None
        self.posicao_alvo_destino_ataque = None
        self.ordem_ataque = None
        self.atacantes_recebidos.clear()
        self.busca_automatica_bloqueada = True

    def pode_adquirir_alvo_automaticamente(self):
        if not self.busca_automatica_bloqueada:
            return True

        if self.personagem is None:
            return False

        distancia = hypot(
            self.personagem.x - self.personagem.destino_x,
            self.personagem.y - self.personagem.destino_y,
        )

        if distancia <= 6:
            self.busca_automatica_bloqueada = False
            return True

        return False

    def _obter_inimigo_atacando_construcao(self, personagem):
        """Consulta atacantes registrados nas construções próximas."""
        indice = getattr(self.cenario_principal, "indice_espacial", None)
        if indice is None:
            construcoes = getattr(self.cenario_principal, "construcoes", ()) + getattr(
                self.cenario_principal, "construcoes_hostis", ()
            )
        else:
            construcoes = indice.consultar_raio(
                personagem.x,
                personagem.y,
                self.RAIO_DETECCAO_INIMIGO,
                grupos=("construcoes",),
            )

        registro_personagem = self.cenario_principal.obter_entidade(personagem)
        config_personagem = obter_config(personagem.nome)
        faccao = (
            registro_personagem.get("faccao")
            if registro_personagem is not None
            and registro_personagem.get("faccao") is not None
            else config_personagem.get("faccao")
        )

        melhor_atacante = None
        melhor_distancia = None

        for construcao in construcoes:
            for atacante in tuple(getattr(construcao, "atacantes_ativos", ())):
                if atacante is personagem or getattr(atacante, "vida", 0) <= 0:
                    continue
                registro = self.cenario_principal.obter_entidade(atacante)
                if registro is None:
                    continue
                faccao_atacante = registro.get("faccao")
                if faccao_atacante == faccao or (
                    faccao is None and faccao_atacante is None
                ):
                    continue
                distancia = hypot(atacante.x - personagem.x, atacante.y - personagem.y)
                if distancia > self.RAIO_DETECCAO_INIMIGO:
                    continue
                if melhor_distancia is None or distancia < melhor_distancia:
                    melhor_atacante = atacante
                    melhor_distancia = distancia

        metricas = getattr(self.cenario_principal, "metricas_desempenho", None)
        if metricas is not None:
            metricas.contar("buscas_atacante_construcao")
        return melhor_atacante

    def _alvo_e_construcao(self, alvo):
        if alvo is None:
            return False

        entity = self.cenario_principal.obter_entidade(alvo)

        if entity is None:
            return False

        return entity.get("grupo") == "construcoes"

    def tentar_adquirir_inimigo_proximo(self, personagem):
        self.personagem = personagem

        # As caveiras patrulham normalmente antes da missão, mas não iniciam
        # combate por conta própria. O combate antecipado só acontece quando
        # o jogador realmente agride uma delas, caso em que o próprio fluxo de
        # dano já chama iniciar() diretamente.
        if (
            getattr(personagem, "nome", None) == "esqueleto"
            and not self._pode_caveira_adquirir_alvo_automaticamente()
        ):
            return False

        if self.entidade_alvo is not None:
            return False

        if personagem.vida <= 0:
            return False

        registro_personagem = self.cenario_principal.obter_entidade(personagem)
        config_personagem = obter_config(personagem.nome)
        faccao = (
            registro_personagem.get("faccao")
            if registro_personagem is not None
            and registro_personagem.get("faccao") is not None
            else config_personagem.get("faccao")
        )

        # Se um inimigo estiver atacando uma construção, ele tem prioridade
        # absoluta sobre a própria construção como alvo automático.
        inimigo_atacando_construcao = self._obter_inimigo_atacando_construcao(
            personagem
        )

        if inimigo_atacando_construcao is not None:
            self.iniciar(inimigo_atacando_construcao, personagem)
            return True

        self._obter_atacantes()
        if self.atacantes_recebidos:
            proximo_atacante = min(
                self.atacantes_recebidos,
                key=lambda atacante: (
                    getattr(atacante, "vida", float("inf")),
                    self.atacantes_recebidos.get(atacante, float("inf")),
                ),
            )
            self.iniciar(proximo_atacante, personagem)
            return True

        indice = getattr(self.cenario_principal, "indice_espacial", None)
        if indice is not None:
            personagens = indice.consultar_raio(
                personagem.x,
                personagem.y,
                self.RAIO_DETECCAO_INIMIGO,
                grupos=("personagens", "hostis"),
            )
        else:
            personagens = [
                item["entidade"]
                for item in self.cenario_principal.entidades
                if item["grupo"] in ("personagens", "hostis")
            ]

        melhor_personagem = self._obter_melhor_alvo(personagem, personagens, faccao)

        if melhor_personagem is not None:
            self.iniciar(melhor_personagem, personagem)
            return True

        if indice is not None:
            construcoes = indice.consultar_raio(
                personagem.x,
                personagem.y,
                self.RAIO_DETECCAO_INIMIGO,
                grupos=("construcoes",),
            )
        else:
            construcoes = [
                item["entidade"]
                for item in self.cenario_principal.entidades
                if item["grupo"] == "construcoes"
            ]

        melhor_construcao = self._obter_melhor_alvo(personagem, construcoes, faccao)

        if melhor_construcao is None:
            return False

        self.iniciar(melhor_construcao, personagem)
        return True

    def _pode_caveira_adquirir_alvo_automaticamente(self):
        conversa = getattr(self.cenario_principal, "conversa_controller", None)
        estado = getattr(conversa, "estado", None)
        return estado in {"combate_esqueletos"}

    def _obter_melhor_alvo(self, personagem, candidatos, faccao):
        melhor_alvo = None
        melhor_distancia = None

        for candidato in candidatos:
            metricas = getattr(self.cenario_principal, "metricas_desempenho", None)
            if metricas is not None:
                metricas.contar("candidatos_busca_alvo")
            if candidato is personagem:
                continue

            if candidato is getattr(
                self.cenario_principal,
                "construcao_arrastando",
                None,
            ):
                continue

            if getattr(candidato, "vida", 0) <= 0:
                continue

            entity = self.cenario_principal.obter_entidade(candidato)
            if entity is None:
                continue

            faccao_alvo = entity.get("faccao")

            if faccao_alvo == faccao:
                continue

            if faccao is None and faccao_alvo is None:
                continue

            distancia = hypot(
                candidato.x - personagem.x,
                candidato.y - personagem.y,
            )

            if distancia > self.RAIO_DETECCAO_INIMIGO:
                continue

            if melhor_distancia is None or distancia < melhor_distancia:
                melhor_alvo = candidato
                melhor_distancia = distancia

        return melhor_alvo

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        if self._alvo_e_construcao(self.entidade_alvo):
            inimigo_atacando_construcao = self._obter_inimigo_atacando_construcao(
                self.personagem
            )

            if inimigo_atacando_construcao is not None:
                self._trocar_alvo_combate(inimigo_atacando_construcao)

        if (
            self.entidade_alvo is None
            or self._alvo_e_construcao(self.entidade_alvo)
            or not self._atacante_ainda_e_uma_ameaca(self.entidade_alvo)
        ):
            self._atualizar_alvo_por_ataques_recebidos()

        if self.entidade_alvo is None:
            return

        if (
            self.personagem.animacoes.esta_em("atacando")
            or self.personagem.animacoes.esta_em("atacando1")
            or self.personagem.animacoes.esta_em("atacando2")
        ):
            self._interagir(dt)
        else:
            self._andar(dt)

    # ============================================================
    # PRIORIZAÇÃO DE COMBATE
    # ============================================================

    def registrar_atacante(self, atacante):
        if atacante is None or atacante is self.personagem:
            return

        ctrl = self.cenario_principal.controladores.get(atacante)
        ordem = None

        if ctrl is not None:
            atacar = ctrl.get("acoes", {}).get("atacar")

            if atacar is not None:
                usecase = atacar.get("usecase")
                ordem = getattr(usecase, "ordem_ataque", None)

        if ordem is None:
            ordem = self._proxima_ordem_ataque()

        self.atacantes_recebidos.setdefault(atacante, ordem)

    def _esta_fugindo_entidade(self, personagem):
        return False

    def _atacante_ainda_e_uma_ameaca(self, atacante):
        if atacante is None:
            return False

        if getattr(atacante, "vida", 0) <= 0:
            return False

        ctrl = self.cenario_principal.controladores.get(atacante)

        if ctrl is None:
            return False

        atacar = ctrl.get("acoes", {}).get("atacar")

        if atacar is None:
            return False

        usecase = atacar.get("usecase")

        if usecase is None:
            return False

        return usecase.entidade_alvo is self.personagem

    def _obter_atacantes(self):
        removidos = []

        for atacante in self.atacantes_recebidos:
            if not self._atacante_ainda_e_uma_ameaca(atacante):
                removidos.append(atacante)

        for atacante in removidos:
            self.atacantes_recebidos.pop(atacante, None)

        itens = sorted(
            self.atacantes_recebidos.items(),
            key=lambda item: item[1],
        )

        return [atacante for atacante, _ in itens]

    def _atualizar_alvo_por_ataques_recebidos(self):
        atacantes = self._obter_atacantes()

        if not atacantes:
            return

        escolhido = min(
            atacantes,
            key=lambda atacante: (
                getattr(atacante, "vida", float("inf")),
                self.atacantes_recebidos.get(atacante, float("inf")),
            ),
        )

        if self.entidade_alvo is not escolhido:
            self._trocar_alvo_combate(escolhido)

    def _trocar_alvo_combate(self, novo_alvo):
        if novo_alvo is None or novo_alvo is self.personagem:
            return

        self._desregistrar_alvo_ativo(self.entidade_alvo)
        self.entidade_alvo = novo_alvo
        self._registrar_alvo_ativo(self.entidade_alvo)
        self.posicao_alvo_no_inicio_ataque = None
        self.destino_ataque = None
        self.posicao_alvo_destino_ataque = None

        # Não altere a orientação aqui. O personagem pode precisar contornar
        # obstáculos antes de chegar ao alvo. O movimento real define o flip.
        self._animacao_correndo()

    # ============================================================
    # MOVIMENTAÇÃO / ATAQUE
    # ============================================================

    def _alvo_ainda_esta_no_alcance(self):
        if self.posicao_alvo_no_inicio_ataque is None:
            return True

        alvo_x, alvo_y = self.posicao_alvo_no_inicio_ataque

        deslocamento_alvo = hypot(
            self.entidade_alvo.x - alvo_x,
            self.entidade_alvo.y - alvo_y,
        )

        return deslocamento_alvo <= self.DISTANCIA_DESLOCAMENTO_PARA_PERSEGUIR

    def _esta_fugindo(self):
        return self._esta_fugindo_entidade(self.entidade_alvo)

    def _calcular_destino_ataque(self):
        alvo = self.entidade_alvo
        if alvo is None:
            return self.personagem.x, self.personagem.y

        posicao_alvo = (alvo.x, alvo.y)

        if (
            self.destino_ataque is not None
            and self.posicao_alvo_destino_ataque is not None
            and hypot(
                alvo.x - self.posicao_alvo_destino_ataque[0],
                alvo.y - self.posicao_alvo_destino_ataque[1],
            )
            <= 8
            and self.navegacao.pode_andar(
                self.destino_ataque[0],
                self.destino_ataque[1],
                self.personagem.altura,
            )
        ):
            # Durante a perseguição, a orientação visual deve seguir o
            # deslocamento real pela rota, e não o alvo final. O alvo pode
            # estar do outro lado de um barranco/obstáculo enquanto o próximo
            # waypoint exige movimento em outra direção. O MoverPersonagemUseCase
            # atualizará o flip com base no deslocamento efetivo deste frame.
            return self.destino_ataque

        entity = self.cenario_principal.obter_entidade(alvo)

        if entity is not None and entity.get("grupo") == "construcoes":
            rect = self.cenario_principal.obter_rect_colisao(alvo)
            destino = self.navegacao.encontrar_ponto_acessivel_ao_redor_rect(
                self.personagem.x,
                self.personagem.y,
                rect,
                self.personagem.altura,
                margem=self.DISTANCIA_ATAQUE_CONSTRUCAO,
            )
        else:
            alvo_caminhavel = self.navegacao.pode_andar(
                alvo.x,
                alvo.y,
                self.personagem.altura,
            )

            if alvo_caminhavel:
                linha_bloqueada = self.navegacao.linha_bloqueada_por_obstaculos(
                    self.personagem.x,
                    self.personagem.y,
                    alvo.x,
                    alvo.y,
                )

                if linha_bloqueada:
                    # Quando uma construção bloqueia a linha até um alvo que
                    # está em terreno caminhável, não basta perseguir o centro
                    # do alvo. Encontramos um ponto acessível bem próximo dele
                    # e com linha de ataque livre. Isso permite que o defensor
                    # faça o contorno e conclua o ataque em vez de ficar preso
                    # na quina da construção.
                    destino = self.navegacao.encontrar_ponto_acessivel_proximo(
                        self.personagem.x,
                        self.personagem.y,
                        alvo.x,
                        alvo.y,
                        self.personagem.altura,
                        distancia=self.DISTANCIA_LATERAL_ATAQUE,
                        distancia_maxima_alvo=self.DISTANCIA_PARADA
                        + self.DISTANCIA_LATERAL_ATAQUE,
                        exigir_linha_livre_ate_alvo=True,
                    )
                    if destino is None:
                        destino = (alvo.x, alvo.y)
                else:
                    destino = (alvo.x, alvo.y)
            else:
                # Alvos podem existir em um tile bloqueado. Nesse caso, não
                # tentamos atravessar o obstáculo: buscamos o ponto caminhável
                # mais próximo que ainda permita atacar o alvo.
                destino = self.navegacao.encontrar_ponto_acessivel_proximo(
                    self.personagem.x,
                    self.personagem.y,
                    alvo.x,
                    alvo.y,
                    self.personagem.altura,
                    distancia=self.DISTANCIA_LATERAL_ATAQUE,
                    distancia_maxima_alvo=self.DISTANCIA_PARADA
                    + self.DISTANCIA_LATERAL_ATAQUE,
                    exigir_linha_livre_ate_alvo=True,
                )
                if destino is None:
                    destino = (alvo.x, alvo.y)

        if destino is None:
            if entity is not None and entity.get("grupo") == "construcoes":
                rect = self.cenario_principal.obter_rect_colisao(alvo)
                px = min(max(self.personagem.x, rect.left), rect.right)
                py = min(max(self.personagem.y, rect.top), rect.bottom)
                dx = self.personagem.x - px
                dy = self.personagem.y - py
                comprimento = hypot(dx, dy) or 1.0
                distancia = self.DISTANCIA_ATAQUE_CONSTRUCAO
                destino = (
                    px + dx / comprimento * distancia,
                    py + dy / comprimento * distancia,
                )
            else:
                destino = (self.personagem.x, self.personagem.y)

        self.destino_ataque = destino
        self.posicao_alvo_destino_ataque = posicao_alvo
        # Não vire para o alvo enquanto ainda estiver se deslocando.
        # A orientação deve acompanhar o caminho efetivamente percorrido.
        return destino

    def _andar(self, dt):
        destino_x, destino_y = self._calcular_destino_ataque()

        entity = self.cenario_principal.obter_entidade(self.entidade_alvo)
        alvo_e_construcao = entity is not None and entity.get("grupo") == "construcoes"

        if alvo_e_construcao:
            rect = self.cenario_principal.obter_rect_colisao(self.entidade_alvo)
            distancia_borda = self.navegacao.distancia_para_rect(
                self.personagem.x,
                self.personagem.y,
                rect,
            )
            pronto_para_atacar = distancia_borda <= self.DISTANCIA_PARADA
        else:
            distancia_real_alvo = hypot(
                self.entidade_alvo.x - self.personagem.x,
                self.entidade_alvo.y - self.personagem.y,
            )
            linha_bloqueada = self.navegacao.linha_bloqueada_por_obstaculos(
                self.personagem.x,
                self.personagem.y,
                self.entidade_alvo.x,
                self.entidade_alvo.y,
            )
            pronto_para_atacar = (
                distancia_real_alvo <= self.DISTANCIA_PARADA and not linha_bloqueada
            )

        if pronto_para_atacar:
            self.tempo = 0.0

            self.posicao_alvo_no_inicio_ataque = (
                self.entidade_alvo.x,
                self.entidade_alvo.y,
            )

            if hasattr(self.personagem.animacoes, "flip_para_direcao"):
                self.flip = self.personagem.animacoes.flip_para_direcao(
                    self.entidade_alvo.x - self.personagem.x
                )
            self._iniciar_ataque()

            return

        # Não escolha o flip pelo alvo antes de mover. O MoverPersonagemUseCase
        # atualizará a animação com base no deslocamento real deste frame.
        self.personagem.destino_x = destino_x
        self.personagem.destino_y = destino_y

        self.cenario_principal.mover_personagem.executar(
            personagem=self.personagem,
            navegacao=self.navegacao,
            velocidade=self.VELOCIDADE,
            dt=dt,
            destino_externo=(destino_x, destino_y),
            animacao_correndo="correndo",
            animacao_parado="ocioso",
        )
        # Mantém o estado interno do combate sincronizado com o controlador
        # visual, evitando que uma orientação antiga seja reaplicada no frame
        # seguinte.
        self.flip = self.personagem.animacoes.flip

    def _interagir(self, dt):
        if self.entidade_alvo is None:
            return

        if self.entidade_alvo.vida <= 0:
            self._finalizar_ataque()
            return

        animacao = self.personagem.animacoes.animacao_atual

        if not self._alvo_ainda_esta_no_alcance():
            if not animacao.golpe_executado:
                return

            self._animacao_correndo()

            self.posicao_alvo_no_inicio_ataque = None

            return

        entity = self.cenario_principal.obter_entidade(self.entidade_alvo)
        if entity is not None and entity.get("grupo") == "construcoes":
            rect = self.cenario_principal.obter_rect_colisao(self.entidade_alvo)
            distancia_real_alvo = self.navegacao.distancia_para_rect(
                self.personagem.x,
                self.personagem.y,
                rect,
            )
        else:
            distancia_real_alvo = hypot(
                self.entidade_alvo.x - self.personagem.x,
                self.entidade_alvo.y - self.personagem.y,
            )

        # Uma vez dentro do alcance de combate, a unidade não deve abandonar
        # o ataque por causa da linha de navegação. Isso era especialmente
        # perceptível nas caveiras: elas golpeavam, faziam um pequeno flip e
        # voltavam a correr embora ainda estivessem exatamente na distância
        # necessária para atacar.
        if distancia_real_alvo > self.DISTANCIA_PARADA:
            self._animacao_correndo()
            self.posicao_alvo_no_inicio_ataque = None
            return

        if not animacao.golpe_executado:
            return

        self._causar_dano()

        self._apos_causar_dano()

    def _causar_dano(self):
        # O combate não aplica mais deslocamento de fuga/empurrão ao alvo.
        # A regra de fuga por pouca vida foi removida e este cálculo também
        # estava fazendo a unidade sair da distância de ataque imediatamente
        # após receber o golpe.
        ctrl = self.cenario_principal.controladores.get(self.entidade_alvo)

        entity = self.cenario_principal.obter_entidade(self.entidade_alvo)

        if entity["grupo"] == "construcoes":
            self.entidade_alvo.receber_golpe()

            # Nem toda construção precisa possuir um controlador de IA.
            # O ataque deve conseguir causar dano normalmente mesmo quando
            # `controladores` não tiver uma entrada para o alvo.
            if ctrl is not None:
                defender = ctrl.get("padrao")
                if defender is not None:
                    defender.iniciar(
                        self.entidade_alvo,
                        self.personagem,
                        entity.get("faccao"),
                    )

            return

        vida_anterior = getattr(self.entidade_alvo, "vida", 0)
        self.entidade_alvo.receber_golpe(
            self.personagem,
            self.entidade_alvo.x,
            self.entidade_alvo.y,
        )
        dano_aplicado = max(0, vida_anterior - getattr(self.entidade_alvo, "vida", 0))
        if dano_aplicado > 0:
            registrar_dano = getattr(
                self.cenario_principal, "registrar_dano_visual", None
            )
            if registrar_dano is not None:
                registrar_dano(self.entidade_alvo, dano_aplicado)

        if ctrl is not None:
            atacar = ctrl["acoes"].get("atacar")

            if atacar is not None:
                atacar["usecase"].registrar_atacante(self.personagem)

        self.chamar_defensores.executar(
            self.entidade_alvo,
            self.personagem,
            entity["faccao"],
        )

        if ctrl is not None:
            atacar = ctrl["acoes"].get("atacar")

            if atacar is not None:
                # Depois de receber um golpe, a unidade continua no combate.
                # A fuga automática por vida baixa foi removida para evitar que
                # o alvo abandone o ciclo de ataque e fique congelado.
                atacar["usecase"].iniciar(
                    self.personagem,
                    self.entidade_alvo,
                )

    def _iniciar_animacao_movimento(self):
        self._animacao_correndo()

    def _finalizar_ataque(self):
        self._desregistrar_alvo_ativo(self.entidade_alvo)
        self.entidade_alvo = None
        self.posicao_alvo_no_inicio_ataque = None
        self.ordem_ataque = None
        self._animacao_ocioso()

    # ============================================================
    # APRESENTAÇÃO GENÉRICA DA UNIDADE
    # ============================================================

    def _definir_animacao(self, nome, flip=None):
        """Define uma animação pelo nome declarado no sprites_config."""
        animacoes = getattr(self.personagem, "animacoes", None)
        if animacoes is None:
            return
        definir = getattr(animacoes, "definir", None)
        if callable(definir):
            definir(nome, flip=self.flip if flip is None else flip)
            return

        estado = f"{nome}_flip" if (self.flip if flip is None else flip) else nome
        animacoes.definir(estado)

    def _possui_animacao(self, nome):
        animacoes = getattr(self.personagem, "animacoes", None)
        return bool(animacoes and nome in getattr(animacoes, "animacoes", {}))

    def _iniciar_ataque(self):
        # Prefere a nomenclatura compartilhada e cai para atacando1 quando
        # necessário. Unidades com sequência/defesa especial podem sobrescrever.
        if self._possui_animacao("atacando"):
            self._definir_animacao("atacando")
            return
        if self._possui_animacao("atacando1"):
            self._definir_animacao("atacando1")
            return
        raise RuntimeError(
            f"Personagem '{getattr(self.personagem, 'nome', 'desconhecido')}' "
            "não possui animação de ataque configurada"
        )

    def _apos_causar_dano(self):
        self._iniciar_ataque()

    def _animacao_correndo(self):
        if self._possui_animacao("correndo"):
            # A direção da corrida deve ser atualizada pelo deslocamento real
            # em MoverPersonagemUseCase. Aqui apenas troca para a animação de
            # corrida preservando o flip já calculado pelo movimento.
            self._definir_animacao("correndo")
        else:
            self._animacao_ocioso()

    def _estado_correndo(self):
        return "correndo"

    def _estado_correndo_flip(self):
        return "correndo_flip"

    def _estado_ocioso(self):
        return "ocioso"

    def _estado_ocioso_flip(self):
        return "ocioso_flip"

    def _animacao_ocioso(self):
        if self._possui_animacao("ocioso"):
            self._definir_animacao("ocioso")
