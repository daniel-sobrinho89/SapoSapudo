from domains.sapudo.pensamentos_sapo import PensamentosSapo


class ProcessarComandoSpotifyUseCase:
    def __init__(self, spotify, desacoplar_violao):
        self.spotify = spotify
        self.desacoplar_violao = desacoplar_violao

    def executar(self, comando_spotify, finalizar_comando):
        acao = comando_spotify["acao"]
        sucesso = self._executar_acao(acao, comando_spotify, finalizar_comando)

        finalizar_comando()

        if not sucesso and acao != "buscar":
            self._mostrar_pensamento_spotify_erro()

    def _executar_acao(self, acao, comando_spotify, finalizar_comando):
        if acao == "pause":
            return self.desacoplar_violao.executar()

        if acao == "play":
            return self.spotify.tocar()

        if acao == "next":
            return self.spotify.proxima()

        if acao == "previous":
            return self.spotify.anterior()

        if acao == "buscar":
            sucesso = self.spotify.buscar_e_tocar(
                comando_spotify.get("pesquisa"), finalizar_comando
            )

            if not sucesso:
                self._mostrar_pensamento_busca()

            if not sucesso and self.spotify.spotify_pendente:
                # O Spotify será aberto e o callback será chamado
                # posteriormente pelo fluxo assíncrono.
                return False

            return sucesso

        return False

    def _mostrar_pensamento_busca(self):
        if not self.spotify.spotify_token:
            PensamentosSapo.publicar("Preciso conhecer seu Spotify primeiro.", 5)
            return

        if self.spotify.spotify_pendente:
            PensamentosSapo.publicar("Abrindo seu Spotify...", 3)

    def _mostrar_pensamento_spotify_erro(self):
        PensamentosSapo.publicar(
            "Não estou conseguindo visitar este universo musical agora.", 6
        )
