from datetime import datetime

from systems.sapudo.maquina_estado_sapo import EstadoSapo, MaquinaEstadoSapo


class AnimacoesSapo:
    def __init__(self):
        # ====================================
        # ESTADOS
        # ====================================
        self.maquina = MaquinaEstadoSapo()

        # ====================================
        # CONTROLE SONO
        # ====================================

        self.iniciou_sono_hoje = False

        # ====================================
        # CONTROLE TROCA DE FRAMES
        # ====================================

        self.parado = Animacao(60, 0.15)
        self.dormir = Animacao(60, 0.15, loop=False)
        self.dormindo = Animacao(9, 0.50)
        self.acordar = Animacao(60, 0.15, loop=False)
        self.pegar_violao = Animacao(15, 0.16, loop=False)
        self.levantar_violao = Animacao(15, 0.14, loop=False)
        self.guardar_violao = Animacao(9, 0.14)
        self.soltar_violao = Animacao(9, 0.14, loop=False)
        self.andar_esquerda = Animacao(10, 0.07)
        self.andar_direita = Animacao(10, 0.07)

        self.ultimo_frame_guardar = -1
        self.parar_audio_violao = False

        self.frame_violao = 0
        self.tempo_violao = 0.0

        self.direcao_violao = 1

        self.frame_min_violao = 0
        self.frame_max_violao = 9

        self.intervalo_violao = 0.22
        self.callback_verificar_spotify = None

        # ====================================
        # ACORDAR (PNG)
        # ====================================

        self.executou_acordar_hoje = False
        self.tempo_tocando_violao = 0

        # ====================================
        # CAMINHADA
        # ====================================

        # horários planejados
        self.horarios_caminhada = [(8, 0), (14, 0), (18, 0)]

        # retry quando não puder caminhar
        self.proxima_tentativa_caminhada = None

        # evita disparar várias vezes no mesmo minuto
        self.ultima_execucao_caminhada = None

    # ====================================
    # SONO
    # ====================================

    def verificar_horario_sono(self):
        agora = datetime.now()

        horario_atual = (agora.hour * 60) + agora.minute

        horario_acordar = (7 * 60) + 30
        horario_dormir = (22 * 60) + 00

        if horario_dormir < horario_acordar:
            return horario_dormir <= horario_atual < horario_acordar

        return horario_atual >= horario_dormir or horario_atual < horario_acordar

    # ====================================
    # UPDATE
    # ====================================

    def atualizar(self, dt):
        agora = datetime.now()

        self.atualizar_pegar_violao(dt)
        self.atualizar_violao(dt)
        self.atualizar_levantar_violao(dt)
        self.atualizar_guardar_violao(dt)
        self.atualizar_soltar_violao(dt)
        self.atualizar_andar_esquerda(dt)
        self.atualizar_andar_direita(dt)

        if self.maquina.eh(EstadoSapo.PARADO):
            self.parado.atualizar(dt)

        if self.maquina.eh(EstadoSapo.ACORDANDO):
            if self.acordar.atualizar(dt):
                self.maquina.trocar(EstadoSapo.PARADO)

            return

        horario_sono = self.verificar_horario_sono()

        if self.maquina.eh(EstadoSapo.ADORMECENDO):
            if not horario_sono:
                self.iniciar_acordar()

                return

            if self.dormir.atualizar(dt):
                self.maquina.trocar(EstadoSapo.DORMINDO)

            return

        # ====================================
        # RESET
        # ====================================
        if agora.hour == 8 and agora.minute == 0:
            self.iniciou_sono_hoje = False
            self.executou_acordar_hoje = False

        if (
            not horario_sono
            and not self.executou_acordar_hoje
            and (self.maquina.em_estado(EstadoSapo.DORMINDO, EstadoSapo.ADORMECENDO))
        ):
            self.iniciar_acordar()
            self.executou_acordar_hoje = True

            return

        # ====================================
        # INICIAR SONO
        # ====================================

        if (
            horario_sono
            and not self.iniciou_sono_hoje
            and not (
                self.maquina.em_estado(EstadoSapo.DORMINDO, EstadoSapo.ADORMECENDO)
            )
        ):
            self.iniciou_sono_hoje = True
            self.iniciar_dormir()

            return

        # ====================================
        # DELAY SONO
        # ====================================

        if self.maquina.eh(EstadoSapo.DORMINDO):
            self.dormindo.atualizar(dt)

    def iniciar_dormir(self):
        self.dormir.reset()
        self.maquina.trocar(EstadoSapo.ADORMECENDO)

    # ====================================
    # ACORDAR
    # ====================================

    def iniciar_acordar(self):
        self.acordar.reset()
        self.maquina.trocar(EstadoSapo.ACORDANDO)

    # ====================================
    # VIOLÃO
    # ====================================

    def atualizar_pegar_violao(self, dt):
        if not self.maquina.eh(EstadoSapo.PEGANDO_VIOLAO):
            return

        if self.pegar_violao.atualizar(dt):
            self.maquina.trocar(EstadoSapo.TOCANDO_VIOLAO)
            self.pegar_violao.reset()
            self.frame_violao = 0
            self.direcao_violao = 1

    def iniciar_violao(self):
        if self.maquina.em_estado(EstadoSapo.TOCANDO_VIOLAO, EstadoSapo.PEGANDO_VIOLAO):
            return

        self.maquina.trocar(EstadoSapo.PEGANDO_VIOLAO)
        self.pegar_violao.reset()
        self.frame_violao = 0
        self.direcao_violao = 1

    def parar_violao(self):
        self.maquina.trocar(EstadoSapo.PARADO)
        self.frame_violao = 0
        self.tempo_tocando_violao = 0
        self.tempo_violao = 0
        self.direcao_violao = 1

    def atualizar_violao(self, dt):
        if not self.maquina.eh(EstadoSapo.TOCANDO_VIOLAO):
            return

        self.tempo_tocando_violao += dt

        if self.tempo_tocando_violao >= 900:  # 900 15 minutos
            self.iniciar_levantar_violao()
            return

        self.tempo_violao += dt

        if self.tempo_violao < self.intervalo_violao:
            return

        self.tempo_violao = 0
        self.frame_violao += self.direcao_violao

        if self.frame_violao >= self.frame_max_violao:
            self.frame_violao = self.frame_max_violao
            self.direcao_violao = -1

        elif self.frame_violao <= self.frame_min_violao:
            self.frame_violao = self.frame_min_violao
            self.direcao_violao = 1

    def iniciar_levantar_violao(self):
        self.maquina.trocar(EstadoSapo.LEVANTANDO_VIOLAO)
        self.levantar_violao.reset()

    def atualizar_levantar_violao(self, dt):
        if not self.maquina.eh(EstadoSapo.LEVANTANDO_VIOLAO):
            return

        if not self.levantar_violao.atualizar(dt):
            return

        spotify_tocando = False

        if self.callback_verificar_spotify:
            spotify_tocando = self.callback_verificar_spotify()

        if spotify_tocando:
            self.maquina.trocar(EstadoSapo.TOCANDO_VIOLAO)
            self.frame_violao = 0
            self.direcao_violao = 1
        else:
            self.maquina.trocar(EstadoSapo.GUARDANDO_VIOLAO)
            self.guardar_violao.reset()
            self.ultimo_frame_guardar = -1

    def atualizar_guardar_violao(self, dt):
        if not self.maquina.eh(EstadoSapo.GUARDANDO_VIOLAO):
            return

        self.guardar_violao.atualizar(dt)

    def atualizar_soltar_violao(self, dt):
        if not self.maquina.eh(EstadoSapo.SOLTANDO_VIOLAO):
            return

        if self.soltar_violao.atualizar(dt):
            self.maquina.trocar(EstadoSapo.PARADO)
            self.tempo_tocando_violao = 0

    def iniciar_andar_esquerda(self):
        if self.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            return

        self.maquina.trocar(EstadoSapo.ANDANDO_ESQUERDA)
        self.andar_esquerda.reset()

    def iniciar_andar_direita(self):
        self.maquina.trocar(EstadoSapo.ANDANDO_DIREITA)
        self.andar_direita.reset()

    def atualizar_andar_esquerda(self, dt):
        if not self.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            return

        self.andar_esquerda.atualizar(dt)

    def atualizar_andar_direita(self, dt):
        if not self.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            return

        self.andar_direita.atualizar(dt)


class Animacao:
    def __init__(self, total_frames, intervalo, loop=True):
        self.frame = 0
        self.tempo = 0.0

        self.total_frames = total_frames
        self.intervalo = intervalo
        self.loop = loop

    def atualizar(self, dt):
        self.tempo += dt

        if self.tempo < self.intervalo:
            return False

        self.tempo -= self.intervalo
        self.frame += 1

        terminou = False

        if self.frame >= self.total_frames:
            terminou = True

            if self.loop:
                self.frame = 0
            else:
                self.frame = self.total_frames - 1

        return terminou

    def reset(self):
        self.frame = 0
        self.tempo = 0
