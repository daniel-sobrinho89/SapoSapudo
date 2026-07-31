from application.coordenador_estado_jogo import CoordenadorEstadoJogo
from application.usecases import AtualizarFluxoSpotifyUseCase
from domains.sapudo.pensamentos_sapo import PensamentosSapo
from domains.voz.reconhecedor_android import ReconhecedorAndroid
from domains.voz.roteador_voz import RoteadorVoz


class ControladorVozMusical:
    """
    Coordena o reconhecimento de voz, integração com Spotify e
    comportamentos musicais do Sapo.
    """

    def __init__(
        self,
        spotify,
        audio,
        controle_renderer,
        gerenciador_cenarios,
        clima_service,
        tts,
    ):
        self.spotify = spotify
        self.audio = audio
        self.controle_renderer = controle_renderer
        self.gerenciador_cenarios = gerenciador_cenarios
        self.clima_service = clima_service
        self.tts = tts
        self._pensamento_event = None
        self._pensamentos_aguardo = [
            "Escutando os ecos da lagoa...",
            "As ideias ainda estão borbulhando...",
            "Conversando com os sapos filósofos...",
            "Organizando os girinos do pensamento...",
            "Procurando uma resposta no fundo da lagoa...",
        ]
        self.reconhecedor_voz = ReconhecedorAndroid()
        self.tempo_sem_audio = 0

        self.atualizar_fluxo_spotify = AtualizarFluxoSpotifyUseCase(self.spotify)

        self.coordenador_estado_jogo = CoordenadorEstadoJogo(
            self.clima_service,
            self.spotify,
            self.audio,
            self.gerenciador_cenarios,
        )

    @property
    def inicializado(self):
        return True

    def desligar_microfone(self):
        self.controle_renderer.microfone_ligado = False
        self.tempo_sem_audio = 0
        try:
            self.reconhecedor_voz.ativo_usuario = False
            self.reconhecedor_voz.parar()
            self.reconhecedor_voz.destruir()
        except Exception as ex:
            print(f"[VOZ] Erro ao desligar: {ex}")

        self.reconhecedor_voz = ReconhecedorAndroid()

    def processar_toque_microfone(self, pos_virtual):
        if self.controle_renderer.rect_microfone.collidepoint(pos_virtual):
            self.controle_renderer.microfone_ligado = (
                not self.controle_renderer.microfone_ligado
            )

            if self.controle_renderer.microfone_ligado:
                self.tempo_sem_audio = 0
                self.reconhecedor_voz.ativo_usuario = True
                self.reconhecedor_voz.iniciar()
            else:
                self.reconhecedor_voz.ativo_usuario = False
                self.reconhecedor_voz.parar()

            return True
        return False

    def processar_toque_down(self, pos_virtual):
        # Microfone e Comandos Musicais
        if self.processar_toque_microfone(pos_virtual):
            return

        self.coordenador_estado_jogo.processar_toque_down(pos_virtual)

    def processar_toque_up(self, pos_virtual):
        self.coordenador_estado_jogo.processar_toque_up(pos_virtual)

    def processar_on_touch_move(self, pos_virtual):
        self.coordenador_estado_jogo.processar_on_touch_move(pos_virtual)

    def atualizar(self, dt):
        if self.controle_renderer.microfone_ligado:
            texto = self.reconhecedor_voz.obter_texto()

            if texto:
                print(f"[VOZ] TEXTO: [{texto}]")
                self.tempo_sem_audio = 0

                rota = RoteadorVoz.identificar(texto)
                print(f"[ROTA] {rota}")

                if rota["tipo"] == "spotify":
                    self.coordenador_estado_jogo.executar_comando_spotify(
                        rota["dados"], self.desligar_microfone
                    )

            else:
                self.tempo_sem_audio += dt
                if self.tempo_sem_audio > 10:
                    self.desligar_microfone()

        self.atualizar_fluxo_spotify.executar(dt)
        self.coordenador_estado_jogo.executar(dt)

    def _mostrar_resposta(self, resposta):
        self._parar_pensamentos_aguardo()

        if not resposta:
            return

        PensamentosSapo.publicar(resposta, 30)

        if self.tts:
            self.tts.falar(resposta)

    def _parar_pensamentos_aguardo(self):
        if self._pensamento_event:
            self._pensamento_event.cancel()
            self._pensamento_event = None


class ControladorVozMusicalNulo:
    @property
    def inicializado(self):
        return False

    def atualizar(self, dt):
        pass

    def processar_toque_up(self, pos_virtual):
        pass

    def processar_toque_down(self, *args):
        pass

    def processar_on_touch_move(self, pos_virtual):
        pass

    def processar_toque_microfone(self, *args):
        pass
