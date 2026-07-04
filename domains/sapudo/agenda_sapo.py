# =====================================
# domains.sapudo/agenda_sapo.py
# =====================================

from datetime import datetime


class AgendaSapo:
    """
    Gerencia os horários de rotina do Sapo (sono, caminhada, reset diário).
    """

    def __init__(self):
        self.horarios_caminhada = [(8, 0), (14, 0), (18, 0)]
        self.ultima_execucao_caminhada = None
        self.proxima_tentativa_caminhada = None

        self.iniciou_sono_hoje = False
        self.executou_acordar_hoje = False
        self.data_ultimo_reset = datetime.now().date()

    def verificar_horario_sono(self, agora=None):
        agora = agora or datetime.now()
        horario_atual = (agora.hour * 60) + agora.minute

        horario_acordar = (7 * 60) + 30
        horario_dormir = (22 * 60) + 00

        if horario_dormir < horario_acordar:
            return horario_dormir <= horario_atual < horario_acordar

        return horario_atual >= horario_dormir or horario_atual < horario_acordar

    def deve_iniciar_caminhada(self, agora, horario_atual):
        if self.proxima_tentativa_caminhada:
            return agora >= self.proxima_tentativa_caminhada

        for hora, minuto in self.horarios_caminhada:
            if horario_atual == (hora, minuto):
                chave = (agora.year, agora.month, agora.day, hora, minuto)

                if self.ultima_execucao_caminhada != chave:
                    self.ultima_execucao_caminhada = chave
                    return True

        return False

    def atualizar_resets_diarios(self, agora=None):
        agora = agora or datetime.now()
        if agora.hour >= 8 and self.data_ultimo_reset != agora.date():
            self.iniciou_sono_hoje = False
            self.executou_acordar_hoje = False
            self.data_ultimo_reset = agora.date()
            return True
        return False
