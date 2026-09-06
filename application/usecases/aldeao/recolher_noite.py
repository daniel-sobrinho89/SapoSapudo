from contextlib import suppress
from math import hypot

from utils.config import TILE_SIZE


class RecolherBernardoUseCase:
    HORA_INICIO_NOITE = 18.0
    HORA_INICIO_MANHA = 6.0
    DISTANCIA_CHEGADA = 28.0
    RAIO_BUSCA_ARVORE = TILE_SIZE * 10
    VELOCIDADE = 48

    def __init__(self, cenario, obter_casa, obter_arvore):
        self.cenario = cenario
        self.obter_casa = obter_casa
        self.obter_arvore = obter_arvore
        self.ativo = False
        self.dormindo = False
        self.voltando_para_inicio = False
        self.destino = None
        self.destino_inicial = None
        self.tipo_destino = None

    @property
    def dormindo_ou_recolhendo(self):
        return self.ativo

    def atualizar(self, dt, hora, bernardo):
        if bernardo is None:
            self.cancelar()
            return

        noite = hora >= self.HORA_INICIO_NOITE or hora < self.HORA_INICIO_MANHA

        if self.dormindo:
            if not noite:
                self._iniciar_retorno_ao_inicio(bernardo)
            return

        if self.voltando_para_inicio:
            self._atualizar_retorno_ao_inicio(bernardo, dt)
            return

        if not self.ativo:
            if noite:
                self._iniciar(bernardo)
            return

        if not noite:
            self._cancelar_recolhimento()
            return

        if self.destino is None:
            self._iniciar(bernardo)
            return

        x, y = self.destino
        if hypot(bernardo.x - x, bernardo.y - y) <= self.DISTANCIA_CHEGADA:
            with suppress(Exception):
                self.cenario.mover_personagem.cancelar_rota(bernardo)
            bernardo.destino_x = bernardo.x
            bernardo.destino_y = bernardo.y
            bernardo.animacoes.definir_por_direcao(
                "ocioso",
                x - bernardo.x,
            )
            bernardo.visivel = False
            self.dormindo = True
            return

        self.cenario.mover_personagem.executar(
            personagem=bernardo,
            navegacao=self.cenario.navegacao,
            velocidade=self.VELOCIDADE,
            estado_correndo="correndo",
            estado_correndo_flip="correndo_flip",
            estado_parado="ocioso",
            estado_parado_flip="ocioso_flip",
            dt=dt,
            destino_externo=self.destino,
        )
        dx = self.destino[0] - bernardo.x
        bernardo.animacoes.definir_por_direcao("correndo", dx)

    def _iniciar(self, bernardo):
        casa = self.obter_casa()
        if casa is not None:
            destino = self._ponto_frente(casa)
            tipo = "casa"
        else:
            arvore = self.obter_arvore(bernardo)
            destino = self._ponto_frente(arvore) if arvore is not None else None
            tipo = "arvore"

        if destino is None:
            return

        self.ativo = True
        self.dormindo = False
        self.voltando_para_inicio = False
        self.destino = destino
        self.tipo_destino = tipo
        bernardo.destino_x, bernardo.destino_y = destino

    def _ponto_frente(self, entidade):
        if entidade is None:
            return None

        candidatos = (
            (entidade.x, entidade.y + 96),
            (entidade.x - 96, entidade.y + 24),
            (entidade.x + 96, entidade.y + 24),
            (entidade.x, entidade.y - 96),
            (entidade.x - 64, entidade.y + 64),
            (entidade.x + 64, entidade.y + 64),
        )
        bernardo = self.cenario.conversa_controller.bernardo
        altura = getattr(bernardo, "altura", 0) if bernardo is not None else 0

        for x, y in candidatos:
            try:
                if self.cenario.navegacao.pode_andar(x, y, altura):
                    return x, y
            except Exception:
                continue
        return candidatos[0]

    def _iniciar_retorno_ao_inicio(self, bernardo):
        with suppress(Exception):
            self.cenario.mover_personagem.cancelar_rota(bernardo)

        destino = self.destino_inicial
        if destino is None:
            destino = getattr(bernardo, "posicao_inicial", None)
        if destino is None:
            destino = (bernardo.x, bernardo.y)

        self.destino = (destino[0], destino[1])
        self.voltando_para_inicio = True
        self.dormindo = False
        self.ativo = True
        bernardo.visivel = True
        bernardo.destino_x, bernardo.destino_y = self.destino

    def _atualizar_retorno_ao_inicio(self, bernardo, dt):
        if self.destino is None:
            self._finalizar_retorno_ao_inicio(bernardo)
            return

        x, y = self.destino
        if hypot(bernardo.x - x, bernardo.y - y) <= self.DISTANCIA_CHEGADA:
            self._finalizar_retorno_ao_inicio(bernardo)
            return

        self.cenario.mover_personagem.executar(
            personagem=bernardo,
            navegacao=self.cenario.navegacao,
            velocidade=self.VELOCIDADE,
            estado_correndo="correndo",
            estado_correndo_flip="correndo_flip",
            estado_parado="ocioso",
            estado_parado_flip="ocioso_flip",
            dt=dt,
            destino_externo=self.destino,
        )
        dx = self.destino[0] - bernardo.x
        bernardo.animacoes.definir_por_direcao("correndo", dx)

    def _finalizar_retorno_ao_inicio(self, bernardo):
        with suppress(Exception):
            self.cenario.mover_personagem.cancelar_rota(bernardo)

        bernardo.x, bernardo.y = self.destino
        bernardo.base_pe_y = bernardo.y
        bernardo.destino_x = bernardo.x
        bernardo.destino_y = bernardo.y
        bernardo.visivel = True

        bernardo.animacoes.definir(
            "ocioso",
            flip=bernardo.flip,
        )

        self.ativo = False
        self.dormindo = False
        self.voltando_para_inicio = False
        self.destino = None
        self.tipo_destino = None

    def _cancelar_recolhimento(self):
        self.ativo = False
        self.dormindo = False
        self.voltando_para_inicio = False
        self.destino = None
        self.tipo_destino = None

    def cancelar(self):
        bernardo = getattr(self.cenario.conversa_controller, "bernardo", None)
        if bernardo is not None:
            bernardo.visivel = True
        self._cancelar_recolhimento()
