from utils.config import ALTURA, LARGURA
from utils.kivy_adapter import Rect


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

        # A faixa é deliberadamente comum ao desktop e à web. O zoom é aplicado
        # somente na transformação mundo -> tela, nunca no espaço lógico.
        self.zoom = 1.0
        self.zoom_min = 0.9
        self.zoom_max = 2.0

        self.largura = LARGURA
        self.altura = ALTURA
        self.arrastando = False
        self.ultimo_mouse = None
        self.limite_esquerdo = 0.0
        self.limite_inferior = 0.0
        self.limite_direito = None
        self.limite_superior = None

    @property
    def largura_mundo_visivel(self):
        return self.largura / self.zoom

    @property
    def altura_mundo_visivel(self):
        return self.altura / self.zoom

    def definir_limites(self, largura_mundo, altura_mundo, margem_x=0, margem_y=0):
        self.limite_esquerdo = float(margem_x)
        self.limite_inferior = float(margem_y)
        self.limite_direito = max(self.limite_esquerdo, float(largura_mundo) - margem_x)
        self.limite_superior = max(self.limite_inferior, float(altura_mundo) - margem_y)
        self._ajustar_limites()

    def definir_limites_mundo(self, x_min, y_min, x_max, y_max):
        """Define explicitamente os limites físicos do mapa em coordenadas de mundo."""
        self.limite_esquerdo = float(x_min)
        self.limite_inferior = float(y_min)
        self.limite_direito = max(self.limite_esquerdo, float(x_max))
        self.limite_superior = max(self.limite_inferior, float(y_max))
        self._ajustar_limites()

    def seguir(self, entidade):
        # Mantém a entidade no centro e impede que a câmera revele áreas
        # fora do mapa. Isso transforma o mapa em uma área de aventura
        # contida, mesmo que internamente possua mais células que a tela.
        self.x = entidade.x - self.largura_mundo_visivel / 2
        self.y = entidade.y - self.altura_mundo_visivel / 2
        self._ajustar_limites()

    def _ajustar_limites(self):
        if self.limite_direito is None or self.limite_superior is None:
            return
        max_x = max(
            self.limite_esquerdo, self.limite_direito - self.largura_mundo_visivel
        )
        max_y = max(
            self.limite_inferior, self.limite_superior - self.altura_mundo_visivel
        )
        self.x = min(max(self.x, self.limite_esquerdo), max_x)
        self.y = min(max(self.y, self.limite_inferior), max_y)

    def tela(self, x, y):
        return (
            int(round((x - self.x) * self.zoom)),
            int(round((y - self.y) * self.zoom)),
        )

    def visivel(self, x, y, largura, altura):
        largura_visivel = self.largura_mundo_visivel
        altura_visivel = self.altura_mundo_visivel

        sx = x - self.x
        sy = y - self.y

        return not (
            sx + largura < 0
            or sy + altura < 0
            or sx > largura_visivel
            or sy > altura_visivel
        )

    def tela_rect(self, rect):
        return Rect(
            int(round((rect.x - self.x) * self.zoom)),
            int(round((rect.y - self.y) * self.zoom)),
            max(1, int(round(rect.w * self.zoom))),
            max(1, int(round(rect.h * self.zoom))),
        )

    def mundo(self, x, y):
        return (
            x / self.zoom + self.x,
            y / self.zoom + self.y,
        )

    def arrastar(self, dx_tela, dy_tela):
        """Desloca a câmera pelo arrasto em coordenadas da tela.

        O cursor se move em pixels de tela, enquanto x/y da câmera são
        coordenadas de mundo. A conversão por zoom mantém o arrasto visual
        idêntico em desktop, browser e em qualquer nível de aproximação.
        """
        self.x -= dx_tela / self.zoom
        self.y -= dy_tela / self.zoom
        self._ajustar_limites()

    def aproximar(self, foco_tela=None):
        self._alterar_zoom(self.zoom + 0.1, foco_tela)

    def afastar(self, foco_tela=None):
        self._alterar_zoom(self.zoom - 0.1, foco_tela)

    def definir_zoom(self, zoom, foco_tela=None):
        self._alterar_zoom(zoom, foco_tela)

    def _alterar_zoom(self, novo_zoom, foco_tela=None):
        novo_zoom = max(self.zoom_min, min(float(novo_zoom), self.zoom_max))
        if abs(novo_zoom - self.zoom) < 1e-9:
            return

        # Sem um foco explícito, usa o centro da tela. O ponto do mundo que
        # estava no centro permanece no centro depois do zoom, evitando o
        # efeito de o mapa “andar” quando a aproximação muda.
        if foco_tela is None:
            foco_tela = (self.largura / 2, self.altura / 2)

        foco_mundo = self.mundo(*foco_tela)
        self.zoom = novo_zoom

        self.x = foco_mundo[0] - foco_tela[0] / self.zoom
        self.y = foco_mundo[1] - foco_tela[1] / self.zoom
        self._ajustar_limites()
