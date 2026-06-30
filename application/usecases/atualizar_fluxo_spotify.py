class AtualizarFluxoSpotifyUseCase:
    def __init__(self, sapo, violao, spotify):
        self.violao = violao
        self.sapo = sapo
        self.spotify = spotify
        self.spotify_tocando_anterior = False
        self.spotify_abertura_anterior = False

    def executar(self, dt):
        self.spotify.atualizar_spotify(dt)

        spotify_tocando = self.spotify.spotify_tocando_cache
        spotify_pronto = self.spotify.dispositivo_spotify_pronto

        return spotify_tocando, spotify_pronto
