from domains.sapudo.pensamentos_sapo import PensamentosSapo


class ProcessarComandoSpotifyUseCase:
    def __init__(self, spotify, desacoplar_violao):
        self.spotify = spotify
        self.desacoplar_violao = desacoplar_violao

    def executar(self, comando_spotify, finalizar_comando):
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
                comando_spotify.get("pesquisa"), finalizar_comando
            )

            if not sucesso and self.spotify.spotify_pendente:
                # O Spotify será aberto e o callback será chamado
                # posteriormente pelo fluxo assíncrono.
                return

        finalizar_comando()

        if not sucesso and acao != "buscar":
            self._mostrar_pensamento_spotify_erro()

    def _mostrar_pensamento_spotify_erro(self):
        PensamentosSapo.publicar(
            "Não estou conseguindo visitar este universo musical agora.", 6
        )
