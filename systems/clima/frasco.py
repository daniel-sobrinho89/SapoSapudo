import pygame


class FrascoClimatico:

    def __init__(self):

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

        base_original = pygame.image.load(
            "assets/clima/frasco/frasco_base.png"
        ).convert_alpha()

        vidro_original = pygame.image.load(
            "assets/clima/frasco/frasco_vidro.png"
        ).convert_alpha()

        tampa_original = pygame.image.load(
            "assets/clima/frasco/frasco_tampa.png"
        ).convert_alpha()

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

        self.frasco_base = pygame.transform.smoothscale(
            base_crop,
            (
                int(base_crop.get_width() * escala_base),
                int(base_crop.get_height() * escala_base)
            )
        )

        # =====================================
        # VIDRO
        # =====================================

        self.frasco_vidro = pygame.transform.smoothscale(
            vidro_crop,
            (
                int(vidro_crop.get_width() * escala_vidro),
                int(vidro_crop.get_height() * escala_vidro)
            )
        )

        # =====================================
        # TAMPA
        # =====================================

        self.frasco_tampa = pygame.transform.smoothscale(
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

        self.frasco_surface = pygame.Surface(
            (self.largura, self.altura),
            pygame.SRCALPHA
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

        self.area_interna = pygame.Rect(
            self.x + self.area_interna_offset_x,
            self.y + self.area_interna_offset_y,
            self.area_interna_width,
            self.area_interna_height
        )

        self.area_particulas = pygame.Rect(
            self.x + 45,
            self.y + 90,
            self.largura - 130,
            self.frasco_surface.get_height() - 180
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

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, tela, centro_y=None):

        self.atualizar_posicao(centro_y)

        tela.blit(
            self.frasco_surface,
            (self.x, self.y)
        )