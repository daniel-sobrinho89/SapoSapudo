class SaindoDaCasaUseCase:
    def __init__(self, casa_duende_rect):
        self.casa_duende_rect = casa_duende_rect

    def executar(self, dt, duende):
        self._atualizar_saida_casa(dt, duende)

    def _atualizar_saida_casa(self, dt, duende):
        destino_y = self.casa_duende_rect.top - 50
        velocidade = 55

        if duende.y > destino_y:
            duende.y -= velocidade * dt
            return

        duende.y = destino_y

        duende.y = self.casa_duende_rect.top - 50
        self._preparar_duende_fora_casa(duende)

    def _preparar_duende_fora_casa(self, duende):
        duende.animacoes.fator_sono_visual = 0.0
        duende.base_y = duende.y
        duende.velocidade_x = 0
        duende.velocidade_y = 0
        duende.escolher_novo_destino()
        duende.iniciar_voo()
