from textwrap import wrap

import utils.kivy_adapter as kivy_adapter


class ConversaRenderer:
    LARGURA_PAINEL = 944
    ALTURA_PAINEL = 190
    AVATAR_X_OFFSET = 95
    AVATAR_Y_OFFSET = 105

    def __init__(self, tela, renderers, criar_avatar):
        self.tela = tela
        self.renderers = renderers
        self.criar_avatar = criar_avatar
        self.aberta = False
        self.linhas = []
        self.indice = 0
        self.avatar_tipo = "avatar_aldeao"
        self.nome = ""
        self.concluida_callback = None
        self.avatar_aldeao = criar_avatar("avatar_aldeao")
        self.avatar_sapudo = criar_avatar("avatar_soldado")
        self.avatar_bandido = criar_avatar("avatar_bandido")

    @property
    def linha_atual(self):
        if not self.aberta or self.indice >= len(self.linhas):
            return None
        return self.linhas[self.indice]

    @staticmethod
    def _normalizar_linha(linha):
        """Aceita linhas de diálogo como dict ou tupla (falante, nome, texto)."""
        if isinstance(linha, dict):
            return {
                "falante": linha.get("falante", "aldeao"),
                "nome": linha.get("nome", ""),
                "texto": linha.get("texto", ""),
            }

        if isinstance(linha, (tuple, list)):
            falante = linha[0] if len(linha) > 0 else "aldeao"
            nome = linha[1] if len(linha) > 1 else ""
            texto = linha[2] if len(linha) > 2 else ""
            return {
                "falante": falante,
                "nome": nome,
                "texto": texto,
            }

        return {
            "falante": "aldeao",
            "nome": "",
            "texto": str(linha),
        }

    def iniciar(self, linhas, concluida_callback=None):
        self.linhas = [self._normalizar_linha(linha) for linha in linhas]
        self.indice = 0
        self.aberta = bool(self.linhas)
        self.concluida_callback = concluida_callback

    def avancar(self):
        if not self.aberta:
            return
        self.indice += 1
        if self.indice >= len(self.linhas):
            self.fechar()

    def fechar(self):
        callback = self.concluida_callback
        self.aberta = False
        self.linhas = []
        self.indice = 0
        self.concluida_callback = None
        if callable(callback):
            callback()

    def renderizar(self):
        if not self.aberta:
            return

        x = (1024 - self.LARGURA_PAINEL) // 2
        y = 30
        h = self.ALTURA_PAINEL

        kivy_adapter.draw.rect(
            self.tela,
            (22, 27, 33, 242),
            kivy_adapter.Rect(x, y, self.LARGURA_PAINEL, h),
        )
        kivy_adapter.draw.rect(
            self.tela,
            (216, 188, 128, 255),
            kivy_adapter.Rect(x, y, self.LARGURA_PAINEL, h),
            width=3,
        )

        linha = self.linha_atual
        if linha is None:
            return

        falando = linha.get("falante", "aldeao")
        nome = linha.get("nome", "")
        texto = linha.get("texto", "")
        eh_sapudo = falando == "sapudo"
        eh_bandido = falando == "bandido"

        if eh_sapudo:
            avatar = self.avatar_sapudo
            avatar_tipo = "avatar_soldado"
        elif eh_bandido:
            avatar = self.avatar_bandido
            avatar_tipo = "avatar_bandido"
        else:
            avatar = self.avatar_aldeao
            avatar_tipo = "avatar_aldeao"
        entidade = avatar

        entidade.x = x + 55
        entidade.y = y + 58

        if avatar_tipo in self.renderers:
            renderer = self.renderers[avatar_tipo]
            if renderer.carregado:
                renderer.renderizar(
                    entidade, entidade.animacoes, _CameraUI(), escala=1.0
                )

        texto_x = x + 170

        kivy_adapter.draw.text(self.tela, nome, (texto_x, y + 22), (236, 217, 150), 22)
        for i, parte in enumerate(wrap(texto, width=58)):
            kivy_adapter.draw.text(
                self.tela,
                parte,
                (texto_x, y + 58 + i * 26),
                (245, 245, 245),
                20,
            )

        kivy_adapter.draw.text(
            self.tela,
            "ENTER  continuar",
            (x + self.LARGURA_PAINEL - 205, y + h - 34),
            (180, 190, 200),
            15,
        )


class _CameraUI:
    zoom = 1.0

    def tela(self, x, y):
        return int(x), int(y)

    def visivel(self, x, y, largura, altura):
        return True
