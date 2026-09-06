"""Compatibilidade para a antiga ação de defesa do soldado."""


def defender_soldado(soldado):
    soldado.destino_x = soldado.x
    soldado.destino_y = soldado.y
    soldado.animacoes.definir("defendendo", flip=soldado.animacoes.flip)


__all__ = ["defender_soldado"]
