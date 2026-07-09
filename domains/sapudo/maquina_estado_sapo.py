from enum import Enum


class StateMachine:
    def __init__(self, estado_inicial=None, transicoes_validas=None):
        self.estado = estado_inicial
        self._transicoes_validas = transicoes_validas or {}
        self._callbacks_entrada = {}
        self._callbacks_saida = {}
        self.tempo_no_estado = 0.0

    def definir_transicao_valida(self, origem, destino):
        self._transicoes_validas.setdefault(origem, set()).add(destino)

    def definir_callback_entrada(self, estado, callback):
        self._callbacks_entrada[estado] = callback

    def definir_callback_saida(self, estado, callback):
        self._callbacks_saida[estado] = callback

    def trocar(self, novo_estado):
        if self.estado is None:
            self.estado = novo_estado
            self.tempo_no_estado = 0.0
            self._executar_callback_entrada(novo_estado)
            return True

        if novo_estado == self.estado:
            return False

        if not self._pode_trocar(novo_estado):
            return False

        self._executar_callback_saida(self.estado)
        self.estado = novo_estado
        self.tempo_no_estado = 0.0
        self._executar_callback_entrada(novo_estado)
        return True

    def _pode_trocar(self, novo_estado):
        if not self._transicoes_validas:
            return True

        destinos = self._transicoes_validas.get(self.estado, set())
        return novo_estado in destinos

    def _executar_callback_saida(self, estado):
        callback = self._callbacks_saida.get(estado)
        if callable(callback):
            callback()

    def _executar_callback_entrada(self, estado):
        callback = self._callbacks_entrada.get(estado)
        if callable(callback):
            callback()

    def atualizar(self, dt):
        self.tempo_no_estado += dt

    def eh(self, estado):
        return self.estado == estado

    def em_estado(self, *estados):
        return self.estado in estados


class EstadoSapo(Enum):
    PARADO = "parado"

    ADORMECENDO = "adormecendo"
    DORMINDO = "dormindo"
    ACORDANDO = "acordando"

    PEGANDO_VIOLAO = "pegando_violao"
    TOCANDO_VIOLAO = "tocando_violao"
    LEVANTANDO_VIOLAO = "levantando_violao"
    GUARDANDO_VIOLAO = "guardando_violao"
    CHEGOU_AO_VIOLAO = "chegou_ao_violao"
    SOLTANDO_VIOLAO = "soltando_violao"

    ANDANDO_ESQUERDA = "andando_esquerda"
    ANDANDO_DIREITA = "andando_direita"
    CONVERSAR = "conversar"

    PEGANDO_LIVRO = "pegando_livro"
    LENDO_LIVRO = "lendo_livro"
    LEVANTAR_LIVRO = "levantar_livro"


class MaquinaEstadoSapo(StateMachine):
    def __init__(self):
        super().__init__(EstadoSapo.PARADO)

    def esta_com_violao(self):
        return self.em_estado(
            EstadoSapo.CHEGOU_AO_VIOLAO,
            EstadoSapo.PEGANDO_VIOLAO,
            EstadoSapo.TOCANDO_VIOLAO,
            EstadoSapo.LEVANTANDO_VIOLAO,
            EstadoSapo.GUARDANDO_VIOLAO,
            EstadoSapo.SOLTANDO_VIOLAO,
        )
