class AtualizarFluxoSpotifyUseCase:
    def __init__(self, spotify, buscar_violao):
        self.spotify = spotify
        self.buscar_violao = buscar_violao
        self.spotify_tocando_anterior = False
        self.spotify_pronto_anterior = False

    def executar(self, dt):
        self.spotify.atualizar_spotify(dt)

        spotify_tocando = self.spotify.spotify_tocando_cache
        spotify_pronto = self.spotify.dispositivo_spotify_pronto

        if spotify_tocando != self.spotify_tocando_anterior:
            self.spotify_tocando_anterior = spotify_tocando

            if spotify_tocando:
                self.buscar_violao.executar()

        if spotify_pronto != self.spotify_pronto_anterior:
            self.spotify_pronto_anterior = spotify_pronto

            if spotify_pronto and self.spotify.spotify_pendente and not spotify_tocando:
                self.buscar_violao.executar()

        self.buscar_violao.atualizar()
