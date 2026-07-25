from domains.sapudo.pensamentos_sapo import PensamentosSapo


class AtualizarFluxoSpotifyUseCase:
    def __init__(self, spotify):
        self.spotify = spotify
        self.spotify_tocando_anterior = False
        self.spotify_pronto_anterior = False

    def executar(self, dt):
        self.spotify.atualizar_spotify(dt)

        self._avaliar_fluxo_spotify(
            self.spotify.spotify_tocando_cache,
            self.spotify.dispositivo_spotify_pronto,
        )
        self._avaliar_pensamentos_spotify(dt)

    def _avaliar_fluxo_spotify(self, spotify_tocando, spotify_pronto):
        if spotify_tocando != self.spotify_tocando_anterior:
            self.spotify_tocando_anterior = spotify_tocando

        if spotify_pronto != self.spotify_pronto_anterior:
            self.spotify_pronto_anterior = spotify_pronto

    def _avaliar_pensamentos_spotify(self, dt):
        if not self.spotify.spotify_tocando_cache:
            return

        if (
            not self.spotify.spotify_artista_atual
            and not self.spotify.spotify_musica_atual
        ):
            return

        self.spotify.spotify_pensamento_timer -= dt

        if self.spotify.spotify_pensamento_timer <= 0:
            self.spotify.spotify_pensamento_timer = 10

            novo_pensamento = f"Lá lá lá... {self.spotify.spotify_musica_atual}"
            if self.spotify.spotify_mostrar_artista:
                novo_pensamento = (
                    f"Ihuuu! Estou ouvindo {self.spotify.spotify_artista_atual}"
                )

            PensamentosSapo.publicar(novo_pensamento, 10)
            self.spotify.spotify_mostrar_artista = (
                not self.spotify.spotify_mostrar_artista
            )
