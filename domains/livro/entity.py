from dataclasses import dataclass


class Livro:
    def __init__(self):
        self.x = 0
        self.y = 0

        self.x_inicial = 0
        self.y_inicial = 0

        self.visivel = False
        self.aberto = False

        self.flutuando = True

        self.timer_visivel = 0.0

    def posicionar(self, x, y):
        self.x = x
        self.y = y

    def mostrar(self, x, y, tempo=420):
        self.posicionar(x, y)

        self.x_inicial = x
        self.y_inicial = y

        self.visivel = True
        self.aberto = False
        self.timer_visivel = tempo

    def exibir(self, x=0, y=0, tempo=420):
        self.mostrar(x, y, tempo)

    def ocultar(self):
        self.visivel = False
        self.aberto = False
        self.timer_visivel = 0

    def esconder(self):
        self.ocultar()

    def abrir(self):
        self.visivel = False
        self.aberto = True
        self.timer_visivel = 0

    def abrir_para_leitura(self):
        self.abrir()

    def fechar(self):
        self.aberto = False
        self.timer_visivel = 0

    def fechar_leitura(self):
        self.fechar()

    def atualizar_timer(self, dt):
        if not self.visivel:
            return False

        self.timer_visivel -= dt

        if self.timer_visivel <= 0:
            self.ocultar()
            return True

        return False

    def voltar_origem(self):
        self.x = self.x_inicial
        self.y = self.y_inicial

    def estado(self):
        return EstadoLivro(
            x=self.x,
            y=self.y,
            x_inicial=self.x_inicial,
            y_inicial=self.y_inicial,
            visivel=self.visivel,
            aberto=self.aberto,
            flutuando=self.flutuando,
            timer_visivel=self.timer_visivel,
        )


@dataclass
class EstadoLivro:
    x: float
    y: float

    x_inicial: float
    y_inicial: float

    visivel: bool
    aberto: bool

    flutuando: bool

    timer_visivel: float
