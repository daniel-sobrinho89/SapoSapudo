from PIL import ImageDraw, ImageFont

import kivy_adapter
from domains.sapudo.maquina_estado_sapo import EstadoSapo


class SapoRenderer:
    def __init__(self, tela, assets, transform):
        self.tela = tela
        self.assets = assets
        self.transform = transform

        self.corpo_rect = kivy_adapter.Rect(-1000, -1000, 1, 1)

        self.carregar_assets()

    # =====================================
    # LOAD
    # =====================================

    def carregar_assets(self):
        self.frames_parado = []
        for i in range(60):
            self.frames_parado.append(
                self.assets.carregar(f"sapudo/parado/sapudo_{i:04d}.webp")
            )

        self.frames_acordar = []
        for i in range(60):
            self.frames_acordar.append(
                self.assets.carregar(f"sapudo/acordar/sapudo_{i:04d}.webp")
            )

        self.frames_dormir = self.frames_acordar[::-1]
        self.frames_dormindo = self.frames_acordar[:9][::-1]

        self.frames_pegar_violao = []
        for i in range(15):
            self.frames_pegar_violao.append(
                self.assets.carregar(f"sapudo/pegar_violao/sapudo_{i:04d}.webp")
            )

        self.frames_levantar_violao = self.frames_pegar_violao[::-1]

        self.frames_tocar_violao = []
        for i in range(10):
            self.frames_tocar_violao.append(
                self.assets.carregar(f"sapudo/tocar_violao/sapudo_{i:04d}.webp")
            )

        self.frames_guardar_violao = []
        for i in range(9):
            self.frames_guardar_violao.append(
                self.assets.carregar(f"sapudo/guardar_violao/sapudo_{i:04d}.webp")
            )

        self.frames_soltar_violao = []
        for i in range(9):
            self.frames_soltar_violao.append(
                self.assets.carregar(f"sapudo/soltar_violao/sapudo_{i:04d}.webp")
            )

        self.frames_andar_esquerda = []
        for i in range(10):
            self.frames_andar_esquerda.append(
                self.assets.carregar(f"sapudo/andar_esquerda/sapudo_{i:04d}.webp")
            )

        self.frames_andar_direita = tuple(
            kivy_adapter.transform.flip(frame, True, False)
            for frame in self.frames_andar_esquerda
        )

        self.frames_conversar = []
        for i in range(60):
            self.frames_conversar.append(
                self.assets.carregar(f"sapudo/conversar/sapudo_{i:04d}.webp")
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

    # =====================================
    # RENDER
    # =====================================

    def obter_frame_animacao(self, animacoes):
        if animacoes.maquina.eh(EstadoSapo.ADORMECENDO):
            return self.frames_dormir[animacoes.dormir.frame]
        elif animacoes.maquina.eh(EstadoSapo.DORMINDO):
            return self.frames_dormindo[animacoes.dormindo.frame]
        elif animacoes.maquina.eh(EstadoSapo.ACORDANDO):
            return self.frames_acordar[animacoes.acordar.frame]
        elif animacoes.maquina.eh(EstadoSapo.PEGANDO_VIOLAO):
            return self.frames_pegar_violao[animacoes.pegar_violao.frame]
        elif animacoes.maquina.eh(EstadoSapo.LEVANTANDO_VIOLAO):
            return self.frames_levantar_violao[animacoes.levantar_violao.frame]
        elif animacoes.maquina.eh(EstadoSapo.GUARDANDO_VIOLAO):
            return self.frames_guardar_violao[animacoes.guardar_violao.frame]
        elif animacoes.maquina.eh(EstadoSapo.SOLTANDO_VIOLAO):
            return self.frames_soltar_violao[animacoes.soltar_violao.frame]
        elif animacoes.maquina.eh(EstadoSapo.ANDANDO_ESQUERDA):
            return self.frames_andar_esquerda[animacoes.andar_esquerda.frame]
        elif animacoes.maquina.eh(EstadoSapo.ANDANDO_DIREITA):
            return self.frames_andar_direita[animacoes.andar_direita.frame]
        elif animacoes.maquina.eh(EstadoSapo.CONVERSAR):
            return self.frames_conversar[animacoes.conversar.frame]

        return self.frames_parado[animacoes.parado.frame]

    def renderizar(self, centro_x, centro_y, escala, animacoes):
        if animacoes.maquina.eh(EstadoSapo.TOCANDO_VIOLAO):
            frame = self.frames_tocar_violao[animacoes.frame_violao]

        else:
            frame = self.obter_frame_animacao(animacoes)

        self.draw(frame, centro_x, centro_y, escala)

        largura = int(frame.get_width() * escala)
        altura = int(frame.get_height() * escala)

        self.corpo_rect = kivy_adapter.Rect(
            centro_x - largura // 2, centro_y - altura // 2, largura, altura
        )


class PensamentoSapoRenderer:
    def __init__(self):
        self.fonte = ImageFont.truetype("assets/fonts/DejaVuSans.ttf", 14)

        self.padding_x = 12
        self.padding_y = 8

        self.largura_maxima = 260

    # =====================================
    # MEDIR TEXTO
    # =====================================

    def medir_texto(self, texto):
        bbox = self.fonte.getbbox(texto)

        largura = bbox[2] - bbox[0]
        altura = bbox[3] - bbox[1]

        return largura, altura

    # =====================================
    # QUEBRA DE TEXTO
    # =====================================

    def quebrar_linhas(self, texto):
        palavras = texto.split()

        linhas = []
        linha_atual = ""

        for palavra in palavras:
            teste = palavra if not linha_atual else f"{linha_atual} {palavra}"

            largura, _ = self.medir_texto(teste)

            if largura <= self.largura_maxima:
                linha_atual = teste

            else:
                linhas.append(linha_atual)

                linha_atual = palavra

        if linha_atual:
            linhas.append(linha_atual)

        return linhas

    # =====================================
    # ALPHA
    # =====================================

    def obter_alpha(self, tempo_restante):
        tempo_total = 6

        if tempo_restante > tempo_total:
            return 255

        if tempo_restante > 5:
            fade = tempo_total - tempo_restante
            return int(255 * fade)

        if tempo_restante < 1:
            return int(255 * tempo_restante)

        return 255

    # =====================================
    # RENDER
    # =====================================

    def renderizar(self, tela, sapo):
        pensamento = sapo.pensamentos

        if not pensamento.texto:
            return

        novo_pensamento = pensamento.texto
        if len(novo_pensamento) > 100:
            novo_pensamento = novo_pensamento[:100].rsplit(" ", 1)[0] + "..."

        linhas = self.quebrar_linhas(novo_pensamento)

        _, altura_linha = self.medir_texto("Ag")

        largura_texto = max(self.medir_texto(linha)[0] for linha in linhas)

        largura_caixa = largura_texto + self.padding_x * 2

        altura_caixa = len(linhas) * altura_linha + self.padding_y * 2

        x = sapo.x - largura_caixa // 2

        y = sapo.y - 100

        alpha = self.obter_alpha(pensamento.tempo_restante)

        surface = kivy_adapter.Surface(
            (largura_caixa, altura_caixa), kivy_adapter.SRCALPHA
        )

        draw = ImageDraw.Draw(surface._img)

        # sombra

        draw.rounded_rectangle(
            (3, 3, largura_caixa, altura_caixa),
            radius=12,
            fill=(0, 0, 0, int(alpha * 0.25)),
        )

        # fundo

        draw.rounded_rectangle(
            (0, 0, largura_caixa - 1, altura_caixa - 1),
            radius=12,
            fill=(250, 248, 242, alpha),
        )

        # borda

        draw.rounded_rectangle(
            (0, 0, largura_caixa - 1, altura_caixa - 1),
            radius=12,
            outline=(180, 180, 180, alpha),
            width=1,
        )

        pos_y = self.padding_y

        for linha in linhas:
            draw.text(
                (self.padding_x, pos_y),
                linha,
                font=self.fonte,
                fill=(40, 40, 40, alpha),
            )

            pos_y += altura_linha

        tela.blit(surface, (int(x), int(y)))
