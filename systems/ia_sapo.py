# =====================================
# systems/ia_sapo.py
# =====================================

import random


class IASapo:

    # Comportamento simples e leve — mecanismo de decisões de alto nível
    def __init__(self):
        self.tempo_decisao = 0.0
        self.proxima_decisao = random.uniform(6.0, 12.0)

    def obter_acao(self, dt):
        self.tempo_decisao += dt

        if self.tempo_decisao >= self.proxima_decisao:
            self.tempo_decisao = 0.0
            self.proxima_decisao = random.uniform(6.0, 12.0)
            # atualmente não tomamos decisões automáticas — placeholder
            return None

        return None
