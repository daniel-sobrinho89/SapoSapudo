from math import hypot

from application.usecases.personagem.chamar_defensores import (
    ChamarDefensoresUseCase,
)
from core.game_config import obter_config
from utils.config import TILE_SIZE


class AtacarPersonagemUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    DISTANCIA_DESLOCAMENTO_PARA_PERSEGUIR = 40
    DISTANCIA_LATERAL_ATAQUE = 45
    TEMPO_MINIMO_ATAQUE = 0.25
    RAIO_DETECCAO_INIMIGO_EM_TILES = 4
    RAIO_DETECCAO_INIMIGO = RAIO_DETECCAO_INIMIGO_EM_TILES * TILE_SIZE

    _sequencia_ataques = 0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.entidade_alvo = None
        self.personagem = None

        self.tempo = 0.0
        self.flip = False
        self.posicao_alvo_no_inicio_ataque = None
        self.ordem_ataque = None
        self.atacantes_recebidos = {}
        self.chamar_defensores = ChamarDefensoresUseCase(cenario_principal)

    @classmethod
    def _proxima_ordem_ataque(cls):
        cls._sequencia_ataques += 1
        return cls._sequencia_ataques

    def iniciar(self, personagemalvo, personagem):
        mesmo_alvo = self.entidade_alvo is personagemalvo

        self.tempo = 0.0
        self.entidade_alvo = personagemalvo
        self.personagem = personagem
        self.posicao_alvo_no_inicio_ataque = None

        if not mesmo_alvo or self.ordem_ataque is None:
            self.ordem_ataque = self._proxima_ordem_ataque()

        self._iniciar_animacao_movimento()

    def cancelar(self):
        self.entidade_alvo = None
        self.posicao_alvo_no_inicio_ataque = None
        self.ordem_ataque = None

    def _obter_inimigo_atacando_construcao(self, personagem):
        faccao = obter_config(personagem.nome).get("faccao")
        melhor_atacante = None
        melhor_distancia = None

        construcoes = (
            self.cenario_principal.construcoes
            + self.cenario_principal.construcoes_hostis
        )

        for construcao in construcoes:
            ctrl_construcao = self.cenario_principal.controladores.get(construcao)

            if ctrl_construcao is None:
                continue

            defender = ctrl_construcao.get("padrao")

            if defender is None:
                continue

            atacante = getattr(defender, "entidade_alvo", None)

            if atacante is None or atacante is personagem:
                continue

            if getattr(atacante, "vida", 0) <= 0:
                continue

            entity = self.cenario_principal.obter_entidade(atacante)

            if entity is None:
                continue

            faccao_atacante = entity.get("faccao")

            if faccao_atacante == faccao:
                continue

            if faccao is None and faccao_atacante is None:
                continue

            distancia = hypot(
                atacante.x - personagem.x,
                atacante.y - personagem.y,
            )

            if distancia > self.RAIO_DETECCAO_INIMIGO:
                continue

            if melhor_distancia is None or distancia < melhor_distancia:
                melhor_atacante = atacante
                melhor_distancia = distancia

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

        if self.entidade_alvo is not None:
            return False

        if personagem.vida <= 0:
            return False

        faccao = obter_config(personagem.nome).get("faccao")

        # Se um inimigo estiver atacando uma construção, ele tem prioridade
        # absoluta sobre a própria construção como alvo automático.
        inimigo_atacando_construcao = self._obter_inimigo_atacando_construcao(
            personagem
        )

        if inimigo_atacando_construcao is not None:
            self.iniciar(inimigo_atacando_construcao, personagem)
            return True

        personagens = [
            item["entidade"]
            for item in self.cenario_principal.entidades
            if item["grupo"] in ("personagens", "hostis")
        ]

        melhor_personagem = self._obter_melhor_alvo(
            personagem,
            personagens,
            faccao,
        )

        if melhor_personagem is not None:
            self.iniciar(melhor_personagem, personagem)
            return True

        construcoes = [
            item["entidade"]
            for item in self.cenario_principal.entidades
            if item["grupo"] == "construcoes"
        ]

        melhor_construcao = self._obter_melhor_alvo(
            personagem,
            construcoes,
            faccao,
        )

        if melhor_construcao is None:
            return False

        self.iniciar(melhor_construcao, personagem)
        return True

    def _obter_melhor_alvo(self, personagem, candidatos, faccao):
        melhor_alvo = None
        melhor_distancia = None

        for candidato in candidatos:
            if candidato is personagem:
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

        # Se estiver indo para uma construção e surgir/continuar existindo
        # um inimigo atacando uma construção, interrompe o avanço e foca nele.
        if self._alvo_e_construcao(self.entidade_alvo):
            inimigo_atacando_construcao = self._obter_inimigo_atacando_construcao(
                self.personagem
            )

            if inimigo_atacando_construcao is not None:
                self._trocar_alvo_combate(inimigo_atacando_construcao)

        self._atualizar_alvo_por_ataques_recebidos()

        if self.entidade_alvo is None:
            return

        if self.personagem.animacoes.maquina.atacando():
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
        return personagem.vida < personagem.VIDA_MINIMA

    def _atacante_ainda_e_uma_ameaca(self, atacante):
        if atacante is None:
            return False

        if getattr(atacante, "vida", 0) <= 0:
            return False

        if self._esta_fugindo_entidade(atacante):
            return True

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
        """
        Aplica as quatro regras do foco de combate.

        1. Se o alvo atual é uma construção e existe um agressor, ataca o
           agressor.
        2. Com dois ou mais agressores, prioriza quem iniciou primeiro.
        3. Se o primeiro agressor está fugindo e existe outro agressor, troca
           para o outro.
        4. Se existe apenas um agressor, continua perseguindo-o mesmo fugindo.
        """
        atacantes = self._obter_atacantes()

        if not atacantes:
            return

        alvo_atual = self.entidade_alvo

        if len(atacantes) == 1:
            escolhido = atacantes[0]

            if alvo_atual is not escolhido:
                self._trocar_alvo_combate(escolhido)

            return

        escolhido = next(
            (
                atacante
                for atacante in atacantes
                if not self._esta_fugindo_entidade(atacante)
            ),
            None,
        )

        # Se todos estiverem fugindo, mantém o primeiro agressor original.
        if escolhido is None:
            escolhido = atacantes[0]

        if alvo_atual is not escolhido:
            self._trocar_alvo_combate(escolhido)

    def _trocar_alvo_combate(self, novo_alvo):
        if novo_alvo is None or novo_alvo is self.personagem:
            return

        self.entidade_alvo = novo_alvo
        self.posicao_alvo_no_inicio_ataque = None

        self.flip = self.entidade_alvo.x < self.personagem.x

        if not self.personagem.animacoes.maquina.atacando():
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
        self.flip = alvo.x < self.personagem.x

        # Construções são obstáculos para o movimento, portanto o destino de
        # ataque nunca pode ser o centro da construção. Calculamos o ponto de
        # aproximação pela borda real da construção, mantendo a unidade fora
        # da área bloqueada.
        if self._alvo_e_construcao(alvo):
            rect = self.cenario_principal.obter_rect_colisao(alvo)
            margem = max(
                self.DISTANCIA_PARADA,
                self.DISTANCIA_LATERAL_ATAQUE,
            )

            if self.flip:
                destino_x = rect.right + margem
            else:
                destino_x = rect.left - margem

            destino_y = max(
                rect.top - self.DISTANCIA_PARADA,
                min(
                    alvo.y,
                    rect.bottom + self.DISTANCIA_PARADA,
                ),
            )
            return destino_x, destino_y

        if self.flip:
            destino_x = alvo.x + self.DISTANCIA_LATERAL_ATAQUE
        else:
            destino_x = alvo.x - self.DISTANCIA_LATERAL_ATAQUE

        return destino_x, alvo.y

    def _andar(self, dt):
        destino_x, destino_y = self._calcular_destino_ataque()

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            self.tempo = 0.0

            self.posicao_alvo_no_inicio_ataque = (
                self.entidade_alvo.x,
                self.entidade_alvo.y,
            )

            self._iniciar_ataque()

            return

        self._animacao_correndo()

        self.personagem.destino_x = destino_x
        self.personagem.destino_y = destino_y

        self.cenario_principal.mover_personagem.executar(
            personagem=self.personagem,
            navegacao=self.cenario_principal.navegacao,
            velocidade=self.VELOCIDADE,
            estado_correndo=self._estado_correndo(),
            estado_correndo_flip=self._estado_correndo_flip(),
            estado_parado=self._estado_ocioso(),
            estado_parado_flip=self._estado_ocioso_flip(),
            dt=dt,
        )

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

        if not animacao.golpe_executado:
            return

        self._causar_dano()

        self._apos_causar_dano()

    def _causar_dano(self):
        destino = self.cenario_principal.navegacao.fugir(
            self.entidade_alvo.x,
            self.entidade_alvo.y,
            self.personagem.x,
            self.personagem.y,
            self.personagem.altura,
        )

        ctrl = self.cenario_principal.controladores.get(self.entidade_alvo)

        entity = self.cenario_principal.obter_entidade(self.entidade_alvo)

        if entity["grupo"] == "construcoes":
            self.entidade_alvo.receber_golpe()

            defender = ctrl["padrao"]

            defender.iniciar(
                self.entidade_alvo,
                self.personagem,
                entity["faccao"],
            )

            return

        self.entidade_alvo.receber_golpe(
            self.personagem,
            *destino,
        )

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

            if atacar is not None and not self._esta_fugindo():
                atacar["usecase"].iniciar(
                    self.personagem,
                    self.entidade_alvo,
                )

    def _iniciar_animacao_movimento(self):
        self._animacao_correndo()

    def _finalizar_ataque(self):
        self.entidade_alvo = None
        self.posicao_alvo_no_inicio_ataque = None
        self.ordem_ataque = None
        self._animacao_ocioso()

    # ============================================================
    # MÉTODOS ESPECÍFICOS DA UNIDADE
    # ============================================================

    def _iniciar_ataque(self):
        raise NotImplementedError

    def _apos_causar_dano(self):
        self._iniciar_ataque()

    def _animacao_correndo(self):
        raise NotImplementedError

    def _estado_correndo(self):
        raise NotImplementedError

    def _estado_correndo_flip(self):
        raise NotImplementedError

    def _estado_ocioso(self):
        raise NotImplementedError

    def _estado_ocioso_flip(self):
        raise NotImplementedError

    def _animacao_ocioso(self):
        raise NotImplementedError
