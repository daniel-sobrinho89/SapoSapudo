from utils.config import MINUTOS_24_HORAS


class CicloDiaNoite:
    """Controla a hora do mundo e o nível de iluminação do cenário.

    O relógio é independente do FPS. A luz usa três faixas visuais:
    manhã clara, tarde levemente reduzida e noite escura.
    """

    HORA_INICIAL = 8.0
    DURACAO_CICLO_SEGUNDOS = MINUTOS_24_HORAS * 60
    SEGUNDOS_POR_HORA = DURACAO_CICLO_SEGUNDOS / 24.0

    FATOR_LUZ_MANHA = 1.05
    FATOR_LUZ_TARDE = 0.94
    FATOR_LUZ_NOITE = 0.62

    def __init__(self, hora_inicial=HORA_INICIAL, segundos_por_hora=SEGUNDOS_POR_HORA):
        self.hora = float(hora_inicial) % 24.0
        self.segundos_por_hora = max(0.1, float(segundos_por_hora))
        self._tempo_decorrido = 0.0

    def atualizar(self, dt, multiplicador=1.0):
        dt = max(0.0, float(dt))
        multiplicador = max(0.0, float(multiplicador))
        tempo_real = dt * multiplicador
        self._tempo_decorrido += tempo_real
        self.hora = (self.hora + tempo_real / self.segundos_por_hora) % 24.0

    @property
    def hora_inteira(self):
        return int((self.hora * 60.0 + 1e-7) // 60.0) % 24

    @property
    def minuto(self):
        minutos_totais = int(self.hora * 60.0 + 1e-7) % (24 * 60)
        return minutos_totais % 60

    @property
    def horario_formatado(self):
        return f"{self.hora_inteira:02d}:{self.minuto:02d}"

    @property
    def periodo(self):
        if 6.0 <= self.hora < 12.0:
            return "manha"
        if 12.0 <= self.hora < 18.0:
            return "tarde"
        return "noite"

    @property
    def nivel_luz(self):
        if self.periodo == "manha":
            return self.FATOR_LUZ_MANHA
        if self.periodo == "tarde":
            return self.FATOR_LUZ_TARDE
        return self.FATOR_LUZ_NOITE

    @property
    def chave_iluminacao(self):
        """Chave estável usada pelos renderers para invalidar o cache.

        Como o nível de luz só muda entre manhã, tarde e noite, não há motivo
        para gerar uma nova textura iluminada a cada frame.
        """
        return self.periodo

    def definir_hora(self, hora):
        self.hora = float(hora) % 24.0
        self._tempo_decorrido = 0.0
