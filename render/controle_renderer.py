import utils.kivy_adapter as kivy_adapter


class ControleRenderer:
    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform
        self.microfone_ligado = False

        self.icone_microfone_ligado = self.assets.carregar("ui/microfone_ligado.webp")

        self.icone_microfone_desligado = self.assets.carregar(
            "ui/microfone_desligado.webp"
        )

        self.icone_microfone_ligado = kivy_adapter.transform.scale(
            self.icone_microfone_ligado,
            (
                self.icone_microfone_ligado.get_width() // 3,
                self.icone_microfone_ligado.get_height() // 3,
            ),
        )

        self.icone_microfone_desligado = kivy_adapter.transform.scale(
            self.icone_microfone_desligado,
            (
                self.icone_microfone_desligado.get_width() // 3,
                self.icone_microfone_desligado.get_height() // 3,
            ),
        )

        self.rect_microfone = kivy_adapter.Rect(
            20,
            20,
            self.icone_microfone_ligado.get_width(),
            self.icone_microfone_ligado.get_height(),
        )

    def renderizar(self):
        icone_microfone = (
            self.icone_microfone_ligado
            if self.microfone_ligado
            else self.icone_microfone_desligado
        )

        self.tela.blit(icone_microfone, (self.rect_microfone.x, self.rect_microfone.y))
