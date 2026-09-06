from math import hypot


class ObterOuroUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    TEMPO_OBTENDO = 4.0

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.guardar_recurso_x = 550
        self.guardar_recurso_y = 265

        self.entidade_alvo = None

        self.tempo = 0.0
        self.flip = False

    def iniciar(self, mina, personagem, manual=False):
        self.entidade_alvo = mina
        self.personagem = personagem
        personagem.definir_base_movimento(mina.x, mina.y)

        self.tempo = 0.0

        self.flip = self.personagem.animacoes.flip_para_direcao(
            mina.x - self.personagem.x
        )

        if self.flip:
            self.personagem.animacoes.definir(
                "correndo_picareta", flip=self.personagem.animacoes.flip
            )
        else:
            self.personagem.animacoes.definir("correndo_picareta")

    def cancelar(self):
        self.entidade_alvo = None

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        if self.personagem.animacoes.esta_em("usando_picareta"):
            self._obter(dt)
        elif self.personagem.animacoes.esta_em("correndo_ouro"):
            self._entregar(dt)
        else:
            self._andar(dt)

    # --------------------------------------------------------

    def _andar(self, dt):
        rect = self.entidade_alvo.corpo_rect

        if self.flip:
            destino_x = rect.right + 18.5
        else:
            destino_x = rect.left - 40

        destino_y = rect.bottom - 35

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y
        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            self.tempo = 0.0

            if self.flip:
                self.personagem.animacoes.definir(
                    "usando_picareta", flip=self.personagem.animacoes.flip
                )
            else:
                self.personagem.animacoes.definir("usando_picareta")

            return

        if distancia > 0:
            self.personagem.destino_x = destino_x
            self.personagem.destino_y = destino_y

            self.cenario_principal.mover_personagem.executar(
                personagem=self.personagem,
                navegacao=self.cenario_principal.navegacao,
                velocidade=self.VELOCIDADE,
                estado_correndo="correndo_picareta",
                estado_correndo_flip="correndo_picareta_flip",
                estado_parado="ocioso",
                estado_parado_flip="ocioso_flip",
                dt=dt,
            )

    # --------------------------------------------------------

    def _obter(self, dt):
        self.tempo += dt

        if self.tempo < self.TEMPO_OBTENDO:
            return

        self.flip = self.personagem.animacoes.flip_para_direcao(
            self.guardar_recurso_x - self.personagem.x
        )
        self.entidade_alvo.obter_ouro()
        world = getattr(self.cenario_principal, "world_context", None)
        if world is not None:
            world.state.marcar_recurso_coletado(
                getattr(
                    self.entidade_alvo,
                    "world_resource_id",
                    f"mina_ouro:{id(self.entidade_alvo)}",
                )
            )

        if self.flip:
            self.personagem.animacoes.definir(
                "correndo_ouro", flip=self.personagem.animacoes.flip
            )
        else:
            self.personagem.animacoes.definir("correndo_ouro")

    def _entregar(self, dt):
        if self.entidade_alvo.animacoes.esta_em("obtido"):
            self.cenario_principal.remover_personagem(
                self.entidade_alvo, ignorar=self.personagem
            )

        destino_x = self.guardar_recurso_x - 40
        destino_y = self.guardar_recurso_y + 150

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y
        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            if self.flip:
                self.personagem.animacoes.definir(
                    "ocioso", flip=self.personagem.animacoes.flip
                )
            else:
                self.personagem.animacoes.definir("ocioso")

            OFFSET = 40

            if self.flip:
                recurso_x = self.personagem.x - OFFSET
            else:
                recurso_x = self.personagem.x + OFFSET

            recurso_y = self.personagem.y

            self.cenario_principal.carregar_entidade("ouro", recurso_x, recurso_y)
            self.cenario_principal.adicionar_estoque("ouro", 1)

            if self.entidade_alvo.animacoes.esta_em("obtido"):
                self.entidade_alvo = None
            else:
                self.iniciar(self.entidade_alvo, self.personagem)

            return

        self.personagem.destino_x = destino_x
        self.personagem.destino_y = destino_y

        self.cenario_principal.mover_personagem.executar(
            personagem=self.personagem,
            navegacao=self.cenario_principal.navegacao,
            velocidade=self.VELOCIDADE,
            estado_correndo="correndo_ouro",
            estado_correndo_flip="correndo_ouro_flip",
            estado_parado="ocioso",
            estado_parado_flip="ocioso_flip",
            dt=dt,
        )
