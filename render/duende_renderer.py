# =====================================
# render/duende_renderer.py
# =====================================


class DuendeRenderer:
    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform

        self.carregar_assets()

    # =====================================
    # LOAD
    # =====================================

    def carregar_assets(self):
        # =================================
        # BODY
        # =================================

        self.frames_voando = []
        for i in range(15):
            self.frames_voando.append(
                self.assets.carregar(f"assistente/voando/assistente_{i:04d}.webp")
            )

        self.frames_descendo_para_dormir = self.frames_voando[3:14]
        self.frames_dormindo = [self.frames_voando[3]]
        self.frames_guardando_violao = self.frames_voando[0:4]

    def obter_frame_animacao(self, animacoes):
        if animacoes.dormindo:
            return self.frames_dormindo[animacoes.animacao_dormindo.frame]
        elif animacoes.descendo_para_dormir:
            return self.frames_descendo_para_dormir[
                animacoes.animacao_descendo_para_dormir.frame
            ]
        elif animacoes.guardando_violao:
            return self.frames_guardando_violao[
                animacoes.animacao_guardando_violao.frame
            ]

        return self.frames_voando[animacoes.animacao_voando.frame]

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, duende, escala):
        escala *= duende.escala_visual
        frame = self.obter_frame_animacao(duende.animacoes)

        self.draw(
            frame,
            duende.x,
            duende.y,
            escala,
            alpha=duende.alpha_visual,
        )

        largura = int(frame.get_width() * escala)
        altura = int(frame.get_height() * escala)

        duende.atualizar_hitboxes(
            duende.x,
            duende.y,
            largura,
            altura,
        )

    # =====================================
    # DRAW
    # =====================================

    def draw(self, imagem, x, y, escala_x, escala_y=None, alpha=255):
        if escala_y is None:
            escala_y = escala_x

        largura = max(1, int(imagem.get_width() * escala_x))

        altura = max(1, int(imagem.get_height() * escala_y))

        imagem = self.transform.escalar(imagem, (largura, altura))

        imagem.set_alpha(alpha)

        rect = imagem.get_rect(center=(x, y))

        self.tela.blit(imagem, rect)
