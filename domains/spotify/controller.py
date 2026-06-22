import threading

from kivy.clock import Clock

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
        violao,
        spotify,
        audio,
        controle_renderer,
        distancia_violao,
        gerenciador_cenarios=None,
        conversa_sapudo=None,
        tts=None,
    ):
        self.sapo = sapo
        self.violao = violao
        self.spotify = spotify
        self.audio = audio
        self.controle_renderer = controle_renderer
        self.distancia_violao = distancia_violao
        self.gerenciador_cenarios = gerenciador_cenarios
        self.conversa_sapudo = conversa_sapudo
        self.tts = tts

        self.reconhecedor_voz = ReconhecedorAndroid()
        self.tempo_sem_audio = 0

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
        self.sapo.pensamentos.texto = (
            "Não estou conseguindo visitar este universo musical agora."
        )
        self.sapo.pensamentos.tempo_restante = 6

    def iniciar_sequencia_spotify(self):
        self.sapo.buscar_violao(self.violao, self.spotify, self.distancia_violao)

    def iniciar_sequencia_spotify_com_violao(self):
        self.sapo.iniciar_sequencia_spotify_com_violao(self.violao, self.spotify)

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
        if self.violao.acoplado and self.violao.tentar_desacoplar(
            pos_virtual, self.sapo, self.spotify
        ):
            return True

        if renderer_violao.obter_rect(self.violao).collidepoint(pos_virtual):
            self.violao.iniciar_arraste(*pos_virtual)
            return True

        return False

    def processar_toque_up_violao(self):
        return self.violao.finalizar_interacao(
            self.sapo, self.spotify, self.gerenciador_cenarios
        )

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

    def _processar_comando_spotify(self, comando_spotify):
        acao = comando_spotify["acao"]
        sucesso = False

        if acao == "pause":
            sucesso = self.spotify.pausar()
            self.sapo.parar_violao()

        elif acao == "play":
            sucesso = self.spotify.tocar()

        elif acao == "next":
            sucesso = self.spotify.proxima()

        elif acao == "previous":
            sucesso = self.spotify.anterior()

        elif acao == "buscar":
            sucesso = self.spotify.buscar_e_tocar(
                comando_spotify.get("pesquisa"), self.sapo, self.desligar_microfone
            )
            # Se for buscar e ainda estiver pendente/aberto, retornamos cedo
            if not sucesso and self.spotify.spotify_pendente:
                return

        self.desligar_microfone()

        if acao != "pause" and sucesso:
            self.iniciar_sequencia_spotify()
        elif not sucesso and acao != "buscar":
            self.mostrar_pensamento_spotify_erro()

    def _processar_comando_feira(self):
        self.desligar_microfone()
        self.sapo.ir_para_feira()

    def _processar_conversa(self, texto):
        self.desligar_microfone()

        self.sapo.pensamentos.texto = "Escutando os ecos da lagoa..."
        self.sapo.pensamentos.tempo_restante = 10

        print(f"[CONVERSA] pensamento atual: {self.sapo.pensamentos.texto}")

        threading.Thread(
            target=self._executar_gemini,
            args=(texto,),
            daemon=True,
        ).start()

    def _executar_gemini(self, texto):
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

    def _mostrar_resposta(self, resposta):
        if not resposta:
            return

        self.sapo.pensamentos.texto = resposta
        self.sapo.pensamentos.tempo_restante = 30

        if self.tts:
            self.tts.falar(resposta)
