import pygame_adapter


class FrascoClimatico:

    def __init__(
        self,
        transform
    ):

        self.transform = transform
        
        # =====================================
        # POSIÇÃO GLOBAL DO FRASCO
        # =====================================

        self.x = 140
        self.y = 190

        # =====================================
        # ESCALA GLOBAL DO FRASCO
        # =====================================

        self.escala = 0.13

        # =====================================
        # OFFSETS FINOS
        # =====================================

        self.offset_tampa_y = int(55 * self.escala / 0.14)
        self.offset_vidro_y = 0
        self.offset_base_y = int(-120 * self.escala / 0.14)

        self.offset_tampa_x = -3.0
        self.offset_vidro_x = -3.6
        self.offset_base_x = 0

        # =====================================
        # LOAD IMAGENS
        # =====================================

        from render.asset_manager import asset_manager

        base_original = asset_manager.carregar(
            "clima/frasco/frasco_base.png"
        )

        vidro_original = asset_manager.carregar(
            "clima/frasco/frasco_vidro.png"
        )

        tampa_original = asset_manager.carregar(
            "clima/frasco/frasco_tampa.png"
        )

        # =====================================
        # REMOVE ESPAÇOS TRANSPARENTES
        # =====================================

        base_crop = base_original.subsurface(
            base_original.get_bounding_rect()
        ).copy()

        vidro_crop = vidro_original.subsurface(
            vidro_original.get_bounding_rect()
        ).copy()

        tampa_crop = tampa_original.subsurface(
            tampa_original.get_bounding_rect()
        ).copy()

        # =====================================
        # ESCALAS DAS PEÇAS
        # =====================================

        escala_base = self.escala * 0.95
        escala_vidro = self.escala * 1.01
        escala_tampa = self.escala * 0.55

        # =====================================
        # BASE
        # =====================================

        self.frasco_base = self.transform.escalar(
            base_crop,
            (
                int(base_crop.get_width() * escala_base),
                int(base_crop.get_height() * escala_base)
            )
        )

        # =====================================
        # VIDRO
        # =====================================

        self.frasco_vidro = self.transform.escalar(
            vidro_crop,
            (
                int(vidro_crop.get_width() * escala_vidro),
                int(vidro_crop.get_height() * escala_vidro)
            )
        )

        # =====================================
        # TAMPA
        # =====================================

        self.frasco_tampa = self.transform.escalar(
            tampa_crop,
            (
                int(tampa_crop.get_width() * escala_tampa),
                int(tampa_crop.get_height() * escala_tampa)
            )
        )

        # =====================================
        # TAMANHO FINAL DO FRASCO
        # =====================================

        self.largura = max(
            self.frasco_base.get_width(),
            self.frasco_vidro.get_width(),
            self.frasco_tampa.get_width()
        )

        # =====================================
        # POSICIONAMENTO AUTOMÁTICO
        # =====================================

        centro_x = self.largura // 2

        # =====================================
        # VIDRO
        # =====================================
        
        topo_frasco = int(110 * self.escala / 0.13)

        vidro_x = (
            centro_x
            - self.frasco_vidro.get_width() // 2
            + self.offset_vidro_x
        )

        vidro_y = (
            topo_frasco
            + self.offset_vidro_y
        )

        # =====================================
        # BASE
        # =====================================

        base_x = (
            centro_x
            - self.frasco_base.get_width() // 2
            + self.offset_base_x
        )

        base_y = (
            vidro_y
            + int(self.frasco_vidro.get_height() * 0.72)
            + self.offset_base_y
        )

        # =====================================
        # TAMPA
        # =====================================

        tampa_x = (
            vidro_x
            + self.frasco_vidro.get_width()
            - 136
        )

        tampa_y = (
            base_y
            + self.frasco_base.get_height()
            - int(self.frasco_tampa.get_height() * 0.75)
        )

        # =====================================
        # CALCULA ALTURA DINAMICAMENTE
        # =====================================

        altura_base = (
            base_y
            + self.frasco_base.get_height()
        )

        self.altura = int(altura_base + int(50 * self.escala / 0.13))

        # =====================================
        # SURFACE FINAL
        # =====================================

        self.frasco_surface = pygame_adapter.Surface(
            (self.largura, self.altura),
            pygame_adapter.SRCALPHA
        )

        # =====================================
        # BLITS
        # =====================================

        self.frasco_surface.blit(
            self.frasco_vidro,
            (vidro_x, vidro_y)
        )

        self.frasco_surface.blit(
            self.frasco_base,
            (base_x, base_y)
        )

        self.frasco_surface.blit(
            self.frasco_tampa,
            (tampa_x, tampa_y)
        )

        # =====================================
        # ÁREA INTERNA
        # =====================================

        self.area_interna_offset_x = (
            vidro_x
            + int(self.frasco_vidro.get_width() * 0.10)
        )

        self.area_interna_offset_y = (
            vidro_y
            + int(self.frasco_vidro.get_height() * 0.30)
        )

        self.area_interna_width = int(
            self.frasco_vidro.get_width() * 0.80
        )

        self.area_interna_height = int(
            self.frasco_vidro.get_height() * 0.62
        )

        self.area_interna = pygame_adapter.Rect(
            self.x + self.area_interna_offset_x,
            self.y + self.area_interna_offset_y,
            self.area_interna_width,
            self.area_interna_height
        )

        self.area_particulas = pygame_adapter.Rect(
            self.x + 40,
            self.y - 180,
            self.largura - 130,
            self.frasco_surface.get_height() - 180
        )

        # =====================================
        # ÁREA PROTEGIDA DO FRASCO
        # =====================================

        pote_x = (
            self.x
            + vidro_x
            + int(self.frasco_vidro.get_width() * 0.18)
        )

        pote_y = (
            self.y
            + vidro_y
            + int(self.frasco_vidro.get_height() * 0.10)
        )

        pote_w = int(
            self.frasco_vidro.get_width() * 0.67
        )

        pote_h = int(
            self.frasco_vidro.get_height() * 0.55
        )

        self.area_pote = pygame_adapter.Rect(
            pote_x,
            pote_y,
            pote_w,
            pote_h
        )

    # =====================================
    # RENDER
    # =====================================

    def atualizar_posicao(self, centro_y=None):

        if centro_y is not None:

            base_offset = 190

            desired_bottom = centro_y + base_offset

            self.y = int(
                desired_bottom - self.altura
            )

            self.area_interna.x = (
                self.x + self.area_interna_offset_x
            )

            self.area_interna.y = (
                self.y + self.area_interna_offset_y
            )

            self.area_particulas.x = (
                self.x + 40
            )

            self.area_particulas.y = (
                self.y + 40
            )

            self.area_pote.x = (
                self.x
                + self.area_interna_offset_x
                + int(self.area_interna.width * 0.10)
            )

            self.area_pote.y = (
                self.y
                + self.area_interna_offset_y
                - int(self.frasco_vidro.get_height() * 0.07)
            )

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, tela, centro_y=None):

        self.atualizar_posicao(centro_y)

        tela.blit(
            self.frasco_surface,
            (self.x, self.y)
        )