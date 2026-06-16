import threading

from systems.voz.spotify_android import SpotifyAndroid
from systems.voz.spotify_api import SpotifyApi
from systems.voz.spotify_auth import SpotifyAuth
from systems.voz.spotify_callback import SpotifyCallback
from systems.voz.spotify_token_storage import SpotifyTokenStorage


class SpotifyManager:
    def __init__(self):
        self.spotify_token = None
        self.spotify_refresh_token = None
        self.spotify_code_verifier = None
        self.spotify_pendente = None
        self.spotify_pendente_timer = 0
        self.spotify_tentativas = 0
        self.spotify_tocando_cache = False
        self.spotify_cache_timer = 0
        self.spotify_consulta_em_andamento = False
        self.spotify_musica_atual = None
        self.spotify_artista_atual = None
        self.spotify_pensamento_timer = 0
        self.spotify_mostrar_artista = True

    def iniciar(self):
        SpotifyCallback.iniciar()
        dados_spotify = SpotifyTokenStorage.carregar()

        if dados_spotify:
            self.spotify_code_verifier = dados_spotify.get("code_verifier")

            self.spotify_token = dados_spotify.get("access_token")

            self.spotify_refresh_token = dados_spotify.get("refresh_token")
            if self.spotify_refresh_token:
                resposta = SpotifyAuth.renovar_token(self.spotify_refresh_token)
                if resposta:
                    self.spotify_token = resposta.get("access_token")

                    novo_refresh = resposta.get("refresh_token")

                    if novo_refresh:
                        self.spotify_refresh_token = novo_refresh

                    SpotifyTokenStorage.salvar(
                        self.spotify_token,
                        self.spotify_refresh_token,
                        self.spotify_code_verifier,
                    )
                    print("[SPOTIFY] Token renovado")

    def iniciar_login_spotify(self):
        self.spotify_code_verifier = SpotifyAuth.gerar_code_verifier()

        SpotifyTokenStorage.salvar(
            self.spotify_token, self.spotify_refresh_token, self.spotify_code_verifier
        )

        url = SpotifyAuth.obter_url_login(self.spotify_code_verifier)

        SpotifyAndroid.abrir_url(url)

    def renovar_token_spotify(self):
        if not self.spotify_refresh_token:
            return False

        resposta = SpotifyAuth.renovar_token(self.spotify_refresh_token)

        if not resposta:
            return False

        self.spotify_token = resposta.get("access_token")

        novo_refresh = resposta.get("refresh_token")

        if novo_refresh:
            self.spotify_refresh_token = novo_refresh

        SpotifyTokenStorage.salvar(
            self.spotify_token, self.spotify_refresh_token, self.spotify_code_verifier
        )

        print("[SPOTIFY] Token renovado automaticamente")

        return True

    def obter_dispositivo_ativo_com_renovacao(self):
        if not self.spotify_token:
            return None

        device_id = SpotifyApi.obter_dispositivo_ativo(self.spotify_token)
        if device_id == "TOKEN_EXPIRADO" and self.renovar_token_spotify():
            device_id = SpotifyApi.obter_dispositivo_ativo(self.spotify_token)

        return device_id

    # Remover
    # def executar_com_renovacao(self, funcao):
    #     resultado = funcao()
    #     if resultado is not None:
    #         return resultado

    #     if not self.renovar_token_spotify():
    #         return None

    #     return funcao()

    def spotify_esta_tocando(self):
        if not self.spotify_token:
            return False

        resultado = SpotifyApi.esta_tocando(self.spotify_token)
        if resultado is not None:
            return resultado

        if self.renovar_token_spotify():
            resultado = SpotifyApi.esta_tocando(self.spotify_token)
            if resultado is not None:
                return resultado

        return False

    # Remover
    # def spotify_ativo(self):
    #     return self.spotify_token and self.spotify_esta_tocando()

    def atualizar_estado_spotify(self):
        try:
            self.spotify_tocando_cache = self.spotify_esta_tocando()

            if self.spotify_token and self.spotify_tocando_cache:
                dados = SpotifyApi.obter_musica_atual(self.spotify_token)
                if dados:
                    self.spotify_musica_atual = dados["musica"]
                    self.spotify_artista_atual = dados["artista"]

                    if (
                        dados.get("duracao_ms") is not None
                        and dados.get("progresso_ms") is not None
                    ):
                        restante = (dados["duracao_ms"] - dados["progresso_ms"]) / 1000

                        self.spotify_cache_timer = max(10, restante + 2)
                    else:
                        self.spotify_cache_timer = 240
            else:
                self.spotify_musica_atual = None
                self.spotify_artista_atual = None

        except Exception:
            pass
        finally:
            self.spotify_consulta_em_andamento = False

    def atualizar_dados_musica_atual(self):
        if not self.spotify_token:
            return
        try:
            dados = SpotifyApi.obter_musica_atual(self.spotify_token)

            if dados == "TOKEN_EXPIRADO" and self.renovar_token_spotify():
                dados = SpotifyApi.obter_musica_atual(self.spotify_token)

            if dados:
                self.spotify_musica_atual = dados["musica"]
                self.spotify_artista_atual = dados["artista"]
                self.spotify_pensamento_timer = 0
                self.spotify_mostrar_artista = True
        except Exception as ex:
            print(f"[SPOTIFY] Erro ao obter música: {ex}")

    def atualizar_animacao_spotify(self, main, dt, sapo, violao):
        if not violao or not sapo.pode_receber_violao():
            return

        animacoes = sapo.animacoes
        spotify_tocando = self.spotify_tocando_cache

        # =====================================
        # PENSAMENTOS SOBRE A MÚSICA
        # =====================================

        if spotify_tocando and self.spotify_artista_atual and self.spotify_musica_atual:
            self.spotify_pensamento_timer -= dt

            if self.spotify_pensamento_timer <= 0:
                self.spotify_pensamento_timer = 10

                if self.spotify_mostrar_artista:
                    sapo.pensamentos.texto = (
                        f"Ihuuu! Estou ouvindo {self.spotify_artista_atual}"
                    )

                else:
                    sapo.pensamentos.texto = f"Lá lá lá... {self.spotify_musica_atual}"

                sapo.pensamentos.tempo_restante = 10

                self.spotify_mostrar_artista = not self.spotify_mostrar_artista

        # =====================================
        # SPOTIFY TOCANDO
        # =====================================

        if spotify_tocando:
            if not animacoes.maquina.esta_com_violao():
                main.iniciar_sequencia_spotify()

            return

        # =====================================
        # SPOTIFY PAROU
        # =====================================

        if animacoes.maquina.esta_com_violao() and not spotify_tocando:
            animacoes.iniciar_levantar_violao()

    def atualizar_spotify(self, main, dt, sapo, violao):
        self.spotify_cache_timer -= dt
        if self.spotify_cache_timer <= 0 and not self.spotify_consulta_em_andamento:
            self.spotify_consulta_em_andamento = True
            self.spotify_cache_timer = float("inf")
            threading.Thread(target=self.atualizar_estado_spotify, daemon=True).start()

        if self.spotify_pendente:
            self.spotify_pendente_timer -= dt
            if self.spotify_pendente_timer <= 0:
                device_id = self.obter_dispositivo_ativo_com_renovacao()
                if not device_id:
                    self.spotify_tentativas -= 1
                    if self.spotify_tentativas <= 0:
                        self.spotify_pendente = None
                        sapo.pensamentos.texto = "Não encontrei um Spotify ativo."
                        sapo.pensamentos.tempo_restante = 5
                        self.spotify_pendente = None
                        self.spotify_pendente_timer = 0
                        self.spotify_tentativas = 0
                    else:
                        self.spotify_pendente_timer = 5
                else:
                    uri = SpotifyApi.buscar_faixa(
                        self.spotify_token, self.spotify_pendente
                    )
                    if uri:
                        SpotifyApi.transferir_playback(self.spotify_token, device_id)

                        SpotifyAndroid.abrir_spotify()

                        sucesso = SpotifyApi.tocar_faixa(
                            self.spotify_token, device_id, uri
                        )

                        if sucesso:
                            main.iniciar_sequencia_spotify()
                            self.atualizar_dados_musica_atual()
                            self.spotify_tocando_cache = True

                    self.spotify_pendente = None
                    self.spotify_tentativas = 0

        if not self.spotify_token and self.spotify_code_verifier:
            code = SpotifyCallback.obter_code()

            if code:
                resposta = SpotifyAuth.trocar_code_por_token(
                    code, self.spotify_code_verifier
                )

                if resposta:
                    self.spotify_token = resposta["access_token"]

                    self.spotify_refresh_token = resposta["refresh_token"]

                    SpotifyTokenStorage.salvar(
                        self.spotify_token,
                        self.spotify_refresh_token,
                        self.spotify_code_verifier,
                    )

                    if self.spotify_pendente:
                        SpotifyAndroid.abrir_spotify()

                        self.spotify_pendente_timer = 7
                        self.spotify_tentativas = 5

        self.atualizar_animacao_spotify(main, dt, sapo, violao)
