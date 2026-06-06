# =====================================
# entities/sapo.py
# =====================================

import math

from systems.animacoes_sapo import AnimacoesSapo
from systems.respiracao_sapo import RespiracaoSapo
from systems.ia_sapo import IASapo
from systems.system_utils import atualizar_sistemas_basicos

class Sapo:

    def __init__(self, x, y):

        # POSIÇÃO CENTRAL (coordenadas usadas pelo renderer)
        self.x = x
        self.y = y

        self.x_inicial = x
        self.y_inicial = y

        # MOVIMENTO (mantido por compatibilidade futura)
        self.velocidade_x = 0.0
        self.velocidade_y = 0.0

        # SYSTEMS
        self.animacoes = AnimacoesSapo()
        self.respiracao = RespiracaoSapo()
        self.ia = IASapo()

        # FLAGS mínimas
        self.acoplado_violao = False

    # métodos de delegação / API pública
    def iniciar_violao(self):
        self.animacoes.iniciar_violao()

    def parar_violao(self):
        self.animacoes.parar_violao()

    # ponto central de atualização — coordena os systems relacionados ao sapo
    def atualizar(self, dt, ambiente, animacao_folha = None):

        atualizar_sistemas_basicos(
            self.animacoes,
            self.respiracao,
            dt,
            ambiente,
            animacao_folha,
            entity=self,
        )

        # IA (decisões de alto nível)
        self.ia.obter_acao(dt)
