class SaindoDoFrascoUseCase:
    def __init__(self, frasco_rect):
        self.frasco_rect = frasco_rect

    def executar(self, dt, duende):
        self._atualizar_saida_frasco(dt, duende)

    def _atualizar_saida_frasco(self, dt, duende):
        destino_y = self.frasco_rect.top - 50
        velocidade = 55

        if duende.y > destino_y:
            duende.y -= velocidade * dt
            return

        duende.y = destino_y

        duende.y = self.frasco_rect.top - 50
        self._preparar_duende_fora_frasco(duende)

    def _preparar_duende_fora_frasco(self, duende):
        duende.resetar_escala_visual()
        duende.animacoes.fator_sono_visual = 0.0
        duende.base_y = duende.y
        duende.velocidade_x = 0
        duende.velocidade_y = 0
        duende.movimento_bloqueado = False
        duende.escolher_novo_destino()
        duende.animacoes.iniciar_voo()
