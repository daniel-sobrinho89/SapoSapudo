from contextlib import suppress
from math import hypot

from utils.config import TILE_SIZE


class ControlarSapudoManualUseCase:
    """Controle manual do Sapudo, separado da IA dos NPCs."""

    VELOCIDADE = 170.0
    RAIO_ATAQUE = 74.0
    CONE_ATAQUE = 0.15
    TEMPO_ATAQUE = 0.48
    MOMENTO_GOLPE = 0.30
    TEMPO_PERFECT_BLOCK = 0.20

    def __init__(self, cenario):
        self.cenario = cenario
        self.sapudo = None
        self.teclas = set()
        self.ataque_em_andamento = False
        self.tempo_ataque = 0.0
        self.golpe_aplicado = False
        self.proximo_ataque = 1
        self.tempo_ultimo_block = 999.0
        self.tempo_ultimo_q_down = 999.0
        self.INTERVALO_MINIMO_Q = 0.20

    def definir_sapudo(self, sapudo):
        self.sapudo = sapudo

    def tecla_down(self, tecla):
        if self.sapudo is None:
            return
        # Q funciona como alternância. Assim a defesa não depende de um
        # KEYUP específico do backend e nunca fica presa permanentemente.
        if tecla == "q":
            # Q é uma ação de alternância. Não dependemos de KEYUP para
            # permitir a próxima ativação, pois alguns backends/web podem
            # perder o evento de soltura. O pequeno intervalo também impede
            # que o auto-repeat do teclado alterne a defesa várias vezes.
            if self.tempo_ultimo_q_down < self.INTERVALO_MINIMO_Q:
                return
            self.tempo_ultimo_q_down = 0.0
            if self.sapudo.defesa_ativa:
                self.sapudo.defesa_ativa = False
                self.sapudo.perfect_block = False
                self._parar()
            else:
                self.iniciar_defesa()
            return

        self.teclas.add(tecla)

        if tecla == "space":
            self.iniciar_ataque()

    def tecla_up(self, tecla):
        self.teclas.discard(tecla)

    def atualizar(self, dt):
        if self.sapudo is None or self.sapudo.vida <= 0:
            return
        # Durante o descanso dentro da casa, Sapudo fica completamente fora
        # do controle manual até o relógio chegar a 06:30.
        if getattr(self.sapudo, "visivel", True) is False:
            self.teclas.clear()
            self.ataque_em_andamento = False
            return

        self.tempo_ultimo_block += dt
        self.tempo_ultimo_q_down += dt

        if self.cenario.conversa_controller.aberta:
            self.sapudo.defesa_ativa = False
            if not self.ataque_em_andamento:
                self._parar()
            return

        estava_atacando = self.ataque_em_andamento
        self._atualizar_ataque(dt)
        if self.ataque_em_andamento:
            return

        # No browser, pygame normalmente entrega apenas um KEYDOWN para
        # uma tecla mantida pressionada. O Python/Kivy pode repetir o
        # evento, por isso o desktop já parecia atacar continuamente.
        # Mantemos o estado da tecla e iniciamos o próximo golpe assim que
        # a animação anterior termina. Isso deixa os dois backends com o
        # mesmo comportamento: enquanto SPACE estiver pressionado, Sapudo
        # alterna Ataque 1 / Ataque 2 continuamente.
        if estava_atacando and "space" in self.teclas:
            self.iniciar_ataque()
            return

        if self.sapudo.defesa_ativa:
            # Defesa é um modo estável até Q ser pressionado novamente ou o
            # jogador tentar se mover/atacar.
            dx_defesa = any(
                k in self.teclas
                for k in ("left", "a", "right", "d", "up", "w", "down", "s")
            )
            if dx_defesa:
                self._parar()
            else:
                return

        self.sapudo.defesa_ativa = False

        dx = 0
        dy = 0
        if "left" in self.teclas or "a" in self.teclas:
            dx -= 1
        if "right" in self.teclas or "d" in self.teclas:
            dx += 1
        if "up" in self.teclas or "w" in self.teclas:
            dy -= 1
        if "down" in self.teclas or "s" in self.teclas:
            dy += 1

        if dx == 0 and dy == 0:
            self._parar()
            return

        if dx:
            self.sapudo.ultimo_direcao_x = 1 if dx > 0 else -1
        self.sapudo.ultimo_direcao_y = 1 if dy > 0 else -1 if dy < 0 else 0

        comprimento = hypot(dx, dy)
        dx /= comprimento
        dy /= comprimento

        distancia = self.VELOCIDADE * dt
        x_anterior, y_anterior = self.sapudo.x, self.sapudo.y

        self._tentar_mover_eixo(x_anterior + dx * distancia, y_anterior)
        self._tentar_mover_eixo(self.sapudo.x, y_anterior + dy * distancia)

        if self.sapudo.x != x_anterior or self.sapudo.y != y_anterior:
            self.sapudo.destino_x = self.sapudo.x
            self.sapudo.destino_y = self.sapudo.y
            self.sapudo.animacoes.definir(
                "correndo",
                flip=self.sapudo.ultimo_direcao_x < 0,
            )
        else:
            self._parar()

    def iniciar_ataque(self):
        if self.sapudo is None or self.ataque_em_andamento:
            return
        if self.cenario.conversa_controller.aberta or self.sapudo.vida <= 0:
            return

        estado = "atacando1" if self.proximo_ataque == 1 else "atacando2"
        self.sapudo.animacoes.definir(
            estado,
            flip=self.sapudo.ultimo_direcao_x < 0,
        )
        self.ataque_em_andamento = True
        self.tempo_ataque = 0.0
        self.golpe_aplicado = False
        self.ataque_atual = self.proximo_ataque
        self.proximo_ataque = 2 if self.proximo_ataque == 1 else 1

    def iniciar_defesa(self):
        if self.sapudo is None or self.ataque_em_andamento:
            return
        if self.cenario.conversa_controller.aberta or self.sapudo.vida <= 0:
            return
        self.sapudo.animacoes.definir(
            "defendendo",
            flip=self.sapudo.ultimo_direcao_x < 0,
        )
        if not self.sapudo.defesa_ativa:
            self.tempo_ultimo_block = 0.0
        self.sapudo.defesa_ativa = True
        self.sapudo.perfect_block = self.tempo_ultimo_block <= self.TEMPO_PERFECT_BLOCK

    def _atualizar_ataque(self, dt):
        if not self.ataque_em_andamento:
            return

        self.tempo_ataque += dt
        if not self.golpe_aplicado and self.tempo_ataque >= self.MOMENTO_GOLPE:
            self._aplicar_golpe()
            self.golpe_aplicado = True

        if self.tempo_ataque >= self.TEMPO_ATAQUE:
            self.ataque_em_andamento = False
            self._parar()

    def _aplicar_golpe(self):
        melhor = None
        melhor_distancia = None

        candidatos = list(self.cenario.personagens_hostis) + list(
            self.cenario.construcoes_hostis
        )
        for alvo in candidatos:
            if getattr(alvo, "vida", 0) <= 0:
                continue
            dx = alvo.x - self.sapudo.x
            dy = alvo.y - self.sapudo.y
            distancia = hypot(dx, dy)
            if distancia > self.RAIO_ATAQUE:
                continue

            direcao = 1 if dx >= 0 else -1
            if direcao != self.sapudo.ultimo_direcao_x and distancia > TILE_SIZE * 0.7:
                continue

            if melhor is None or distancia < melhor_distancia:
                melhor = alvo
                melhor_distancia = distancia

        if melhor is None:
            return

        if melhor in self.cenario.construcoes_hostis:
            vida_anterior = getattr(melhor, "vida", 0)
            melhor.receber_golpe()
            dano_aplicado = max(0, vida_anterior - getattr(melhor, "vida", 0))
            if dano_aplicado > 0:
                registrar_dano = getattr(self.cenario, "registrar_dano_visual", None)
                if registrar_dano is not None:
                    registrar_dano(melhor, dano_aplicado)
            return

        destino = self.cenario.navegacao.fugir(
            melhor.x,
            melhor.y,
            self.sapudo.x,
            self.sapudo.y,
            self.sapudo.altura,
        )
        vida_anterior = getattr(melhor, "vida", 0)
        melhor.receber_golpe(self.sapudo, *destino)
        dano_aplicado = max(0, vida_anterior - getattr(melhor, "vida", 0))
        if dano_aplicado > 0:
            registrar_dano = getattr(self.cenario, "registrar_dano_visual", None)
            if registrar_dano is not None:
                registrar_dano(melhor, dano_aplicado)

    def _altura_para_posicao(
        self, x, y, altura_atual, x_anterior=None, y_anterior=None
    ):
        obter_transicao = getattr(
            self.cenario.navegacao, "obter_altura_transicao", None
        )
        if obter_transicao is None or x_anterior is None or y_anterior is None:
            return altura_atual

        nova_altura = obter_transicao(x_anterior, y_anterior, x, y, altura_atual)
        return altura_atual if nova_altura is None else nova_altura

    def _pode_mover(self, x, y, altura=None, x_anterior=None, y_anterior=None):
        if altura is None:
            altura = self.sapudo.altura

        navegacao = self.cenario.navegacao
        tilemap = getattr(navegacao, "tilemap", None)

        if tilemap is not None:
            with suppress(Exception):
                col_dest, lin_dest = tilemap.pixel_para_tile(x, y)
                col_orig, lin_orig = (
                    tilemap.pixel_para_tile(x_anterior, y_anterior)
                    if x_anterior is not None and y_anterior is not None
                    else (col_dest, lin_dest)
                )
                envolve_degrau = tilemap.eh_degrau(
                    col_dest, lin_dest
                ) or tilemap.eh_degrau(col_orig, lin_orig)
                if envolve_degrau:
                    return tilemap.pode_andar_pixel(x, y, altura, verificar_borda=False)

        return navegacao.pode_andar(x, y, altura)

    def _tentar_mover_eixo(self, novo_x, novo_y):
        x_anterior, y_anterior = self.sapudo.x, self.sapudo.y
        if novo_x == x_anterior and novo_y == y_anterior:
            return False

        altura_candidata = self._altura_para_posicao(
            novo_x, novo_y, self.sapudo.altura, x_anterior, y_anterior
        )

        if self._pode_mover(novo_x, novo_y, altura_candidata, x_anterior, y_anterior):
            self.sapudo.x = novo_x
            self.sapudo.y = novo_y
            self.sapudo.altura = altura_candidata
            return True

        if altura_candidata != self.sapudo.altura and self._pode_mover(
            novo_x, novo_y, self.sapudo.altura, x_anterior, y_anterior
        ):
            self.sapudo.x = novo_x
            self.sapudo.y = novo_y
            self.sapudo.altura = altura_candidata
            return True

        return False

    def _parar(self):
        if self.sapudo is None:
            return
        self.sapudo.defesa_ativa = False
        self.sapudo.perfect_block = False
        self.sapudo.destino_x = self.sapudo.x
        self.sapudo.destino_y = self.sapudo.y
        self.sapudo.animacoes.definir(
            "ocioso",
            flip=self.sapudo.ultimo_direcao_x < 0,
        )

    def _faccao_sapudo(self):
        registro = self.cenario.obter_entidade(self.sapudo)
        return registro.get("faccao") if registro else None
