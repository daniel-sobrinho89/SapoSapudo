"""Compatibilidade para a antiga ação de defesa do soldado."""

from domains.personagem.maquina_estado_soldado import EstadoSoldado


def defender_soldado(soldado):
    estado = (
        EstadoSoldado.DEFENDENDO_FLIP
        if soldado.animacoes.maquina.flip
        else EstadoSoldado.DEFENDENDO
    )
    soldado.destino_x = soldado.x
    soldado.destino_y = soldado.y
    soldado.animacoes.estado = estado


__all__ = ["defender_soldado"]
