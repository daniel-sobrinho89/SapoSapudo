class DesacoplarViolaoUseCase:
    def __init__(
        self,
        violao,
        sapo,
        spotify,
        audio,
    ):
        self.violao = violao
        self.sapo = sapo
        self.spotify = spotify
        self.audio = audio

    def executar(
        self,
        mouse_pos=None,
        iniciar_arraste=False,
    ):
        if not self.violao.acoplado or (
            mouse_pos and not self.sapo.area_violao().contem(*mouse_pos)
        ):
            return False

        self.violao.acoplado = False
        self.spotify.pausar()
        self.sapo.animacoes.parar_violao()
        self.audio.desligar()
        if iniciar_arraste:
            self.violao.iniciar_arraste(*mouse_pos)

        return True
