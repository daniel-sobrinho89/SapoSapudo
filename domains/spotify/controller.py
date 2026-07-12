import threading

from kivy.clock import Clock

from application.coordenador_estado_jogo import CoordenadorEstadoJogo
from application.usecases import (
    AtualizarFluxoSpotifyUseCase,
    BuscarViolaoUseCase,
    ControlarComportamentoSapoUseCase,
)
from core.platform import IS_ANDROID
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
        sapo,
        duende,
        violao,
        livro,
        spotify,
        audio,
        controle_renderer,
        gerenciador_cenarios,
        clima_service,
        casa_duende,
        esferas,
        evento_livro,
        conversa_sapudo,
        tts,
    ):
        self.sapo = sapo
        self.duende = duende
        self.violao = violao
        self.livro = livro
        self.spotify = spotify
        self.audio = audio
        self.controle_renderer = controle_renderer
        self.gerenciador_cenarios = gerenciador_cenarios
        self.clima_service = clima_service
        self.casa_duende = casa_duende
        self.esferas = esferas
        self.evento_livro = evento_livro
        self.conversa_sapudo = conversa_sapudo
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

        self.buscar_violao = BuscarViolaoUseCase(self.violao, self.sapo)

        self.atualizar_fluxo_spotify = AtualizarFluxoSpotifyUseCase(
            self.spotify, self.buscar_violao
        )

        self.controlar_comportamento_sapo = ControlarComportamentoSapoUseCase(
            self.sapo,
            self.violao,
            self.spotify,
            self.audio,
            self.evento_livro,
            clima_service=self.clima_service,
            tts_service=self.tts,
        )

        self.coordenador_estado_jogo = CoordenadorEstadoJogo(
            self.sapo,
            self.duende,
            self.violao,
            self.livro,
            self.esferas,
            self.clima_service,
            self.casa_duende,
            self.evento_livro,
            self.spotify,
            self.audio,
            self.gerenciador_cenarios,
        )

        Clock.schedule_interval(self._atualizar_status_modelo, 1)

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

    def processar_toque_down(self, pos_virtual, renderer_violao):
        self.coordenador_estado_jogo.processar_toque_down(pos_virtual, renderer_violao)

    def processar_toque_up(self):
        self.coordenador_estado_jogo.processar_toque_up()

    def processar_toque_up_livro(self):
        pass
        # livro_acoplado = self.acoplar_livro.executar(self.sapo.area_livro())
        # if livro_acoplado:
        #     self.resgatar_livro.executar()
        # return livro_acoplado

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

                elif rota["tipo"] == "feira":
                    self._processar_comando_feira()

                elif rota["tipo"] == "conversa":
                    self._processar_conversa(rota["texto"])
            else:
                self.tempo_sem_audio += dt
                if self.tempo_sem_audio > 10:
                    self.desligar_microfone()

        self.controlar_comportamento_sapo.executar(dt)
        self.atualizar_fluxo_spotify.executar(dt)
        self.coordenador_estado_jogo.executar(dt)

    def _processar_comando_feira(self):
        self.desligar_microfone()
        self.controlar_comportamento_sapo.ir_para_feira()
        self.audio.tocar_passeio_sapudo()

    def iniciar_controle_esquerda(self):
        self.controlar_comportamento_sapo.iniciar_controle_esquerda()

    def parar_controle_esquerda(self):
        self.controlar_comportamento_sapo.parar_controle_esquerda()

    def iniciar_controle_direita(self):
        self.controlar_comportamento_sapo.iniciar_controle_direita()

    def parar_controle_direita(self):
        self.controlar_comportamento_sapo.parar_controle_direita()

    def _processar_conversa(self, texto):
        if not self.conversa_sapudo.modelo_pronto:
            PensamentosSapo.publicar(self.conversa_sapudo.model_manager.status, 5)
            return

        if self.conversa_sapudo.processando:
            PensamentosSapo.publicar("Ainda estou pensando na pergunta anterior.", 5)
            return

        self.desligar_microfone()

        PensamentosSapo.publicar("Escutando os ecos da lagoa...", 10)

        self._iniciar_pensamentos_aguardo()

        threading.Thread(
            target=self._executar_client,
            args=(texto,),
            daemon=True,
        ).start()

    def _atualizar_status_modelo(self, dt):
        if not IS_ANDROID:
            return False

        manager = self.conversa_sapudo.model_manager

        if manager.pronto:
            return False

        PensamentosSapo.publicar(manager.status, 2)

        return True

    def _executar_client(self, texto):
        try:
            texto = texto.lower()

            texto = texto.replace("sapado", "sapudo")
            texto = texto.replace("sapo do", "sapudo")
            texto = texto.replace("sabudo", "sapudo")

            for palavra in ("sapudo", "sapo"):
                if texto.startswith(palavra):
                    texto = texto[len(palavra) :].strip()
                    break

            resposta = self.conversa_sapudo.conversar(texto)

            Clock.schedule_once(lambda dt: self._mostrar_resposta(resposta["texto"]))
        except Exception as ex:
            print(f"[GEMINI] Erro: {ex}")

            Clock.schedule_once(
                lambda dt: self._mostrar_resposta("A lagoa ficou silenciosa.")
            )
            Clock.schedule_once(lambda dt: self._parar_pensamentos_aguardo())

    def _mostrar_resposta(self, resposta):
        self._parar_pensamentos_aguardo()

        if not resposta:
            return

        PensamentosSapo.publicar(resposta, 30)

        if self.tts:
            self.tts.falar(resposta)

    def _iniciar_pensamentos_aguardo(self):
        self._parar_pensamentos_aguardo()
        self._indice_pensamento = 0

        def atualizar(dt):
            if not self.conversa_sapudo.processando:
                return False

            self._indice_pensamento = (self._indice_pensamento + 1) % len(
                self._pensamentos_aguardo
            )

            PensamentosSapo.publicar(
                self._pensamentos_aguardo[self._indice_pensamento], 12
            )

            return True

        self._pensamento_event = Clock.schedule_interval(
            atualizar,
            10,
        )

    def _parar_pensamentos_aguardo(self):
        if self._pensamento_event:
            self._pensamento_event.cancel()
            self._pensamento_event = None
