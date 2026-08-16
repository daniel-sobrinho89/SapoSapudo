from domains.personagem.maquina_estado_soldado import EstadoSoldado


class DefenderSoldadoUseCase:
    def executar(self, soldado):
        estado = (
            EstadoSoldado.DEFENDENDO_FLIP
            if soldado.animacoes.maquina.flip
            else EstadoSoldado.DEFENDENDO
        )

        soldado.destino_x = soldado.x
        soldado.destino_y = soldado.y
        soldado.animacoes.estado = estado
