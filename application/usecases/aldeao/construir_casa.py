from math import hypot


class ConstruirCasaUseCase:
    """Controla exclusivamente a construção da casa por Bernardo.

    O use case consome fisicamente as madeiras que foram entregues no ponto
    de construção. Cada unidade é consumida após um intervalo fixo, enquanto
    Bernardo permanece na animação ``usando_martelo``.
    """

    TEMPO_POR_MADEIRA = 1.9
    DISTANCIA_PONTO_CONSTRUCAO = 48

    def __init__(self, cenario):
        self.cenario = cenario
        self.bernardo = None
        self.casa = None
        self.ponto = None
        self.madeira_restante = 0
        self.tempo = 0.0
        self.flip = False
        self.ativo = False
        self._retomada_pendente = False

    def iniciar(self, bernardo, casa, ponto_entrega, quantidade_madeira):
        if bernardo is None or casa is None or ponto_entrega is None:
            return False
        if quantidade_madeira <= 0:
            return False

        self.bernardo = bernardo
        self.casa = casa
        self.ponto = tuple(ponto_entrega)
        self.madeira_restante = int(quantidade_madeira)
        self.tempo = 0.0
        self.ativo = True

        # Durante a construção, Bernardo deve olhar para a casa. A mesma
        # convenção de flip usada pelo restante do jogo é aplicada aqui.
        self.flip = self.bernardo.animacoes.flip_para_direcao(
            self.casa.x - self.bernardo.x
        )
        self._aplicar_orientacao()
        self._parar_bernardo()
        return True

    def retomar(
        self, bernardo, casa, ponto_entrega, quantidade_madeira, tempo=0.0, flip=False
    ):
        """Retoma uma construção a partir de um snapshot salvo.

        Diferente de ``iniciar``, não redefine o tempo já acumulado nem o
        progresso restante. O objetivo é recolocar Bernardo imediatamente no
        estado de martelando, com a mesma construção ativa que existia no save.
        """
        if bernardo is None or casa is None or ponto_entrega is None:
            return False
        quantidade_madeira = int(quantidade_madeira)
        if quantidade_madeira <= 0:
            return False

        self.bernardo = bernardo
        self.casa = casa
        self.ponto = tuple(ponto_entrega)
        self.madeira_restante = quantidade_madeira
        self.tempo = max(0.0, float(tempo))
        self.flip = bool(flip)
        self.ativo = True
        # Marca que este use case acabou de ser reidratado pelo Save/Load.
        # O primeiro tick reestabelece explicitamente o estado operacional.
        self._retomada_pendente = True
        self._aplicar_orientacao()
        self._parar_bernardo()
        return True

    def executar(self, dt):
        if not self.ativo:
            return False

        # O primeiro frame após um Load precisa reentrar explicitamente no
        # estado operacional da construção. Isso é especialmente importante
        # no último pedaço de madeira, quando o save pode acontecer no exato
        # intervalo entre a restauração dos dados e o próximo tick.
        if self._retomada_pendente:
            self._retomada_pendente = False
            if self.bernardo is not None:
                self._parar_bernardo()
                self._aplicar_orientacao()

        if self.bernardo is None or self.casa is None:
            self.cancelar()
            return False

        self._parar_bernardo()

        # Só inicia/continua a animação de martelo enquanto ainda existe
        # madeira para consumir.
        self._aplicar_orientacao()

        self.tempo += max(0.0, dt)
        if self.tempo < self.TEMPO_POR_MADEIRA:
            return True

        self.tempo -= self.TEMPO_POR_MADEIRA

        if not self._consumir_uma_madeira():
            # A madeira entregue não está disponível visualmente ainda.
            # Não perde o progresso da construção: espera e tenta no próximo
            # ciclo.
            return True

        self.madeira_restante -= 1

        if self.madeira_restante <= 0:
            self._concluir()
            return False

        return True

    def _consumir_uma_madeira(self):
        px, py = self.ponto
        candidata = None
        menor = None

        for recurso in getattr(self.cenario, "recursos", ()):
            if getattr(recurso, "nome", None) != "madeira":
                continue
            distancia = hypot(recurso.x - px, recurso.y - py)
            if distancia > self.DISTANCIA_PONTO_CONSTRUCAO:
                continue
            if menor is None or distancia < menor:
                menor = distancia
                candidata = recurso

        if candidata is None:
            return False

        remover = getattr(self.cenario, "remover_personagem", None)
        if callable(remover):
            remover(candidata, ignorar=self.bernardo)
        return True

    def _aplicar_orientacao(self):
        estado = "usando_martelo_flip" if self.flip else "usando_martelo"
        self.bernardo.animacoes.definir(estado)

    def _parar_bernardo(self):
        self.bernardo.destino_x = self.bernardo.x
        self.bernardo.destino_y = self.bernardo.y

    def _concluir(self):
        x, y = self.casa.x, self.casa.y

        remover = getattr(self.cenario, "remover_personagem", None)
        if callable(remover):
            remover(self.casa, ignorar=self.bernardo)

        # Mantém o tipo de casa já definido pelo fluxo da missão.
        carregar = getattr(self.cenario, "carregar_entidade", None)
        if callable(carregar):
            nova_casa = carregar("casa_palha_azul", x, y)
            nova_casa.proprietario_bernardo = True
        else:
            nova_casa = None

        self._parar_bernardo()
        self.bernardo.animacoes.definir(
            "ocioso_flip" if getattr(self.bernardo, "flip", False) else "ocioso"
        )

        self.ativo = False
        callback = getattr(self, "concluida_callback", None)
        if callable(callback):
            callback(nova_casa)

    def cancelar(self):
        self.ativo = False
        self.bernardo = None
        self.casa = None
        self.ponto = None
        self.madeira_restante = 0
        self.tempo = 0.0
        self.flip = False
