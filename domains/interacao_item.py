class ItemInterativo:
    def __init__(self, nome, x, y, descricao, raio=46, tipo_sprite=None):
        self.nome = nome
        self.x = x
        self.y = y
        self.descricao = descricao
        self.raio = raio
        self.coletado = False
        self.tipo_sprite = tipo_sprite or nome
        self.render_rect = None
