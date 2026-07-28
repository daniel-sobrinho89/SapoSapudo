from PIL import ImageDraw, ImageFont

import kivy_adapter
from core.event_bus import PensamentoSapoEvent, event_bus
from domains.sapudo.pensamentos_sapo import PensamentoViewModel


class PensamentoSapoRenderer:
    def __init__(self):
        self.fonte = ImageFont.truetype("assets/fonts/DejaVuSans.ttf", 14)

        self.padding_x = 12
        self.padding_y = 8

        self.largura_maxima = 290
        self.view_model = PensamentoViewModel()

        event_bus.assinar(PensamentoSapoEvent, self.receber_pensamento)

    def receber_pensamento(self, evento):
        if self.view_model.texto:
            return

        self.view_model.texto = evento.texto
        self.view_model.tempo_restante = evento.duracao

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
    def renderizar(self, tela, dt):
        pensamento = self.view_model

        if not pensamento.texto:
            return

        novo_pensamento = pensamento.texto
        if len(novo_pensamento) > 50:
            novo_pensamento = novo_pensamento[:50].rsplit(" ", 1)[0] + "..."

        linhas = self.quebrar_linhas(novo_pensamento)

        _, altura_linha = self.medir_texto("Ag")

        largura_texto = max(self.medir_texto(linha)[0] for linha in linhas)

        largura_caixa = largura_texto + self.padding_x * 2

        altura_caixa = len(linhas) * altura_linha + self.padding_y * 2

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

        # tela.blit(surface, (int(x), int(y)))

        self.view_model.atualizar(dt)
