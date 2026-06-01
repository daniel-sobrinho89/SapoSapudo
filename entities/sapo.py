# =====================================
# entities/sapo.py
# =====================================

import math

from systems.animacoes_sapo import AnimacoesSapo
from systems.respiracao_sapo import RespiracaoSapo
from systems.ia_sapo import IASapo


class Sapo:

    def __init__(self, x, y):

        # POSIÇÃO CENTRAL (coordenadas usadas pelo renderer)
        self.x = x
        self.y = y

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
    def clicar_olho_esquerdo(self):
        self.animacoes.clicar_olho_esquerdo()

    def clicar_olho_direito(self):
        self.animacoes.clicar_olho_direito()

    def iniciar_violao(self):
        self.animacoes.iniciar_violao()

    def parar_violao(self):
        self.animacoes.parar_violao()

    # ponto central de atualização — coordena os systems relacionados ao sapo
    def atualizar(self, dt, frasco_rect, ambiente, animacao_folha):

        # animações (controle visual: piscadas, bocejos, etc.)
        self.animacoes.atualizar(dt)

        # respiração depende do estado de sono
        self.respiracao.atualizar(
            dt,
            self.animacoes.dormindo
        )

        # folha (micro-movimento) recebe intensidade da respiração
        animacao_folha.atualizar(
            dt,
            self.respiracao.intensidade,
            ambiente
        )

        # IA (decisões de alto nível) — atualmente leve e sem efeitos diretos
        self.ia.obter_acao(dt)
