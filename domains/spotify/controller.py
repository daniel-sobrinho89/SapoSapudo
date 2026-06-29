import threading

from kivy.clock import Clock

from application.usecases import (
    AcoplarViolaoUseCase,
    AtualizarFluxoViolaoUseCase,
    BuscarViolaoUseCase,
    DesacoplarViolaoUseCase,
    ResgatarViolaoUseCase,
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
        spotify,
        audio,
        controle_renderer,
        gerenciador_cenarios,
        clima_service,
        frasco_rect,
        conversa_sapudo=None,
        tts=None,
    ):
        self.sapo = sapo
        self.duende = duende
        self.violao = violao
        self.spotify = spotify
        self.audio = audio
        self.controle_renderer = controle_renderer
        self.gerenciador_cenarios = gerenciador_cenarios
        self.clima_service = clima_service
        self.frasco_rect = frasco_rect
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
        self.spotify_tocando_anterior = False
        self.spotify_abertura_anterior = False
        self.reconhecedor_voz = ReconhecedorAndroid()
        self.tempo_sem_audio = 0

        self.acoplar_violao = AcoplarViolaoUseCase(
            self.violao, self.sapo, self.duende, self.spotify
        )
        self.desacoplar_violao = DesacoplarViolaoUseCase(
            self.violao,
            self.sapo,
            self.spotify,
        )
        self.buscar_violao = BuscarViolaoUseCase(self.violao, self.sapo)
        self.atualizar_fluxo_violao = AtualizarFluxoViolaoUseCase(
            self.sapo, self.violao, self.spotify
        )
        self.resgatar_violao = ResgatarViolaoUseCase(
            self.sapo, self.duende, self.clima_service, self.frasco_rect
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

    def mostrar_pensamento_spotify_erro(self):
        PensamentosSapo.publicar(
            "Não estou conseguindo visitar este universo musical agora.", 6
        )

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

    def processar_toque_down_violao(self, pos_virtual, renderer_violao):
        if self.desacoplar_violao.executar(
            mouse_pos=pos_virtual,
            iniciar_arraste=True,
        ):
            return True

        if renderer_violao.obter_rect(self.violao).collidepoint(pos_virtual):
            self.violao.iniciar_arraste(*pos_virtual)
            return True

        return False

    def processar_toque_up_violao(self):
        violao_acoplado = self.acoplar_violao.executar(self.sapo.area_violao())
        if violao_acoplado:
            self.resgatar_violao.executar(self.violao.estado())
        return violao_acoplado

    def atualizar(self, dt):
        if self.controle_renderer.microfone_ligado:
            texto = self.reconhecedor_voz.obter_texto()

            if texto:
                print(f"[VOZ] TEXTO: [{texto}]")
                self.tempo_sem_audio = 0

                rota = RoteadorVoz.identificar(texto)
                print(f"[ROTA] {rota}")

                if rota["tipo"] == "spotify":
                    self._processar_comando_spotify(rota["dados"])

                elif rota["tipo"] == "feira":
                    self._processar_comando_feira()

                elif rota["tipo"] == "conversa":
                    self._processar_conversa(rota["texto"])
            else:
                self.tempo_sem_audio += dt
                if self.tempo_sem_audio > 10:
                    self.desligar_microfone()

        self.spotify.atualizar_estado_spotify(dt)
        self.spotify_tocando = self.spotify.spotify_tocando_cache

        if self.spotify_tocando != self.spotify_tocando_anterior:
            self.spotify_tocando_anterior = self.spotify_tocando

            if self.spotify_tocando:
                self.buscar_violao.executar()

        spotify_pronto = self.spotify.dispositivo_spotify_pronto

        if spotify_pronto != self.spotify_abertura_anterior:
            self.spotify_abertura_anterior = spotify_pronto

            if (
                spotify_pronto
                and self.spotify.spotify_pendente
                and not self.spotify.spotify_tocando_cache
            ):
                self.buscar_violao.executar()

        self.buscar_violao.atualizar()
        self.atualizar_fluxo_violao.executar(dt)
        self.resgatar_violao.atualizar(dt)

    def _processar_comando_spotify(self, comando_spotify):
        acao = comando_spotify["acao"]
        sucesso = False

        if acao == "pause":
            sucesso = self.desacoplar_violao.executar()

        elif acao == "play":
            sucesso = self.spotify.tocar()

        elif acao == "next":
            sucesso = self.spotify.proxima()

        elif acao == "previous":
            sucesso = self.spotify.anterior()

        elif acao == "buscar":
            sucesso = self.spotify.buscar_e_tocar(
                comando_spotify.get("pesquisa"), self.desligar_microfone
            )
            # Se for buscar e ainda estiver pendente/aberto, retornamos cedo
            if not sucesso and self.spotify.spotify_pendente:
                return

        self.desligar_microfone()

        if not sucesso and acao != "buscar":
            self.mostrar_pensamento_spotify_erro()

    def _processar_comando_feira(self):
        self.desligar_microfone()
        self.sapo.ir_para_feira()

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
