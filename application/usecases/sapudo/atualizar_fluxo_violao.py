from domains.sapudo.agenda_sapo import AgendaSapo
from domains.sapudo.maquina_estado_sapo import EstadoSapo


class AtualizarFluxoViolaoUseCase:
    def __init__(self, sapo, violao, spotify, audio):
        self.sapo = sapo
        self.violao = violao
        self.animacoes = sapo.animacoes
        self.spotify = spotify
        self.audio = audio
        self.agenda = AgendaSapo()

    def executar(self, dt):
        maquina = self.animacoes.maquina

        #
        # Chegou o violão
        #
        if maquina.eh(EstadoSapo.CHEGOU_AO_VIOLAO):
            self.animacoes.pegar_violao.reset()
            self.animacoes.violao_logic.resetar()
            maquina.trocar(EstadoSapo.PEGANDO_VIOLAO)
            self.violao.acoplado = True
            return

        #
        # Pegou o violão
        #
        if (
            maquina.eh(EstadoSapo.PEGANDO_VIOLAO)
            and self.animacoes.pegar_violao.frame
            >= self.animacoes.pegar_violao.total_frames - 1
        ):
            self.animacoes.violao_logic.resetar()
            maquina.trocar(EstadoSapo.TOCANDO_VIOLAO)

            if not self.spotify.spotify_tocando_cache:
                self.audio.voltar_musica_fundo()

            return

        #
        # Hora de levantar
        #
        if (
            maquina.eh(EstadoSapo.TOCANDO_VIOLAO)
            and self.animacoes.violao_logic.atualizar_frames(dt) == "levantar"
        ):
            self.animacoes.levantar_violao.reset()
            maquina.trocar(EstadoSapo.LEVANTANDO_VIOLAO)
            self.audio.desligar()

            return

        #
        # Terminou levantar
        #
        if (
            maquina.eh(EstadoSapo.LEVANTANDO_VIOLAO)
            and self.animacoes.levantar_violao.frame
            >= self.animacoes.levantar_violao.total_frames - 1
        ):
            if self.spotify.spotify_tocando_cache:
                self.animacoes.violao_logic.resetar()
                maquina.trocar(EstadoSapo.TOCANDO_VIOLAO)
            else:
                self.animacoes.guardar_violao.reset()
                self.animacoes.ultimo_frame_guardar = -1
                if self.sapo.x < self.violao.x_inicial:
                    self.animacoes.iniciar_andar_direita()
                else:
                    self.animacoes.iniciar_andar_esquerda()
                maquina.trocar(EstadoSapo.GUARDANDO_VIOLAO)
            return

        #
        # Guardando violão
        #
        if maquina.eh(EstadoSapo.GUARDANDO_VIOLAO):
            destino_x = self.violao.x_inicial - 65
            frame_atual = self.animacoes.guardar_violao.frame
            if frame_atual != self.animacoes.ultimo_frame_guardar:
                self.animacoes.ultimo_frame_guardar = frame_atual
                if self.sapo.x < destino_x:
                    self.sapo.x = min(
                        destino_x,
                        self.sapo.x + 3.5,
                    )
                elif self.sapo.x > destino_x:
                    self.sapo.x = max(
                        destino_x,
                        self.sapo.x - 3.5,
                    )
                else:
                    self.animacoes.soltar_violao.reset()
                    maquina.trocar(EstadoSapo.SOLTANDO_VIOLAO)
                    return

                self.violao.x = self.sapo.x + 5
                self.violao.y = self.sapo.y + 20
            return

        #
        # Terminou soltar
        #
        if (
            maquina.eh(EstadoSapo.SOLTANDO_VIOLAO)
            and self.animacoes.soltar_violao.frame
            >= self.animacoes.soltar_violao.total_frames - 1
        ):
            self.violao.voltar_origem()
            maquina.trocar(EstadoSapo.PARADO)
            return
