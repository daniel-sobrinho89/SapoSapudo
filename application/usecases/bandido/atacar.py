from math import hypot

from application.usecases.personagem.atacar import AtacarPersonagemUseCase
from core.game_config import obter_config
from utils.config import TILE_SIZE


class AtacarBandidoUseCase(AtacarPersonagemUseCase):
    """Ataque especial do Bandido: investida em linha reta.

    O bandido não usa o golpe corpo a corpo genérico. Quando decide atacar,
    procura um inimigo alinhado à sua direção e executa uma investida curta.
    Enquanto a investida está em andamento, nenhuma troca de alvo ou nova
    ação pode interromper o golpe.
    """

    DISTANCIA_PARADA = 86
    DISTANCIA_DESLOCAMENTO_PARA_PERSEGUIR = 40
    RAIO_DETECCAO_INIMIGO_EM_TILES = 6
    RAIO_DETECCAO_INIMIGO = RAIO_DETECCAO_INIMIGO_EM_TILES * TILE_SIZE

    LARGURA_LINHA_ATAQUE = 34.0
    DISTANCIA_MAXIMA_INVESTIDA = 155.0
    VELOCIDADE_INVESTIDA = 300.0
    TEMPO_MAXIMO_INVESTIDA = DISTANCIA_MAXIMA_INVESTIDA / VELOCIDADE_INVESTIDA
    INTERVALO_APOS_GOLPE = 0.16

    def __init__(self, cenario_principal):
        super().__init__(cenario_principal)
        self.tempo_apos_golpe = 0.0
        self.investida_ativa = False
        self.investida_decorrido = 0.0
        self.investida_x_inicial = 0.0
        self.investida_y_inicial = 0.0
        self.investida_dx = 1.0
        self.investida_dy = 0.0
        self.investida_distancia_percorrida = 0.0
        self.inimigos_atingidos_na_investida = set()
        self.alvo_golpe_confirmado = None

    def _esta_em_golpe_bloqueante(self):
        return self.investida_ativa or self.tempo_apos_golpe > 0.0

    def iniciar(self, personagemalvo, personagem, manual=False):
        # Uma investida que já começou não aceita troca de alvo nem nova ordem.
        if self.investida_ativa:
            self.personagem = personagem
            return

        if self.tempo_apos_golpe > 0.0 and personagemalvo is self.entidade_alvo:
            self.personagem = personagem
            return

        super().iniciar(personagemalvo, personagem, manual=manual)

    def tentar_adquirir_inimigo_proximo(self, personagem):
        """Adquire um alvo para perseguição, mas o golpe só nasce em linha."""
        self.personagem = personagem

        if self.investida_ativa or self.tempo_apos_golpe > 0.0:
            return False
        if self.entidade_alvo is not None or personagem.vida <= 0:
            return False

        registro_personagem = self.cenario_principal.obter_entidade(personagem)
        config_personagem = obter_config(personagem.nome)
        faccao = (
            registro_personagem.get("faccao")
            if registro_personagem is not None
            and registro_personagem.get("faccao") is not None
            else config_personagem.get("faccao")
        )

        indice = getattr(self.cenario_principal, "indice_espacial", None)
        if indice is not None:
            candidatos = indice.consultar_raio(
                personagem.x,
                personagem.y,
                self.RAIO_DETECCAO_INIMIGO,
                grupos=("personagens", "hostis"),
            )
        else:
            candidatos = [
                item["entidade"]
                for item in self.cenario_principal.entidades
                if item["grupo"] in ("personagens", "hostis")
            ]

        alvo = self._obter_melhor_alvo(personagem, candidatos, faccao)
        if alvo is None:
            return False

        self.iniciar(alvo, personagem)
        return True

    def executar(self, dt):
        if self.personagem is None:
            return

        # Ataque especial tem prioridade absoluta até seu término.
        if self.investida_ativa:
            self._executar_investida(max(0.0, float(dt)))
            return

        if self.tempo_apos_golpe > 0.0:
            self.tempo_apos_golpe = max(0.0, self.tempo_apos_golpe - dt)
            self.personagem.destino_x = self.personagem.x
            self.personagem.destino_y = self.personagem.y
            if self.tempo_apos_golpe <= 0.0:
                self.posicao_alvo_no_inicio_ataque = None
                self.ordem_ataque = None
                if (
                    self.entidade_alvo is not None
                    and getattr(self.entidade_alvo, "vida", 0) > 0
                ):
                    self._animacao_correndo()
                else:
                    self._finalizar_ataque()
            return

        # Enquanto se aproxima, usa a navegação normal. O golpe só inicia
        # quando houver um alvo realmente alinhado na frente do bandido.
        if self.entidade_alvo is None:
            return

        alvo_em_linha = self._obter_alvo_em_linha_de_ataque()
        if alvo_em_linha is not None:
            self.entidade_alvo = alvo_em_linha
            self._iniciar_investida(alvo_em_linha)
            return

        # O alvo atual pode não estar na linha de ataque. O bandido se aproxima
        # normalmente, mas não troca a investida por um golpe lateral.
        self._andar(dt)

    def _obter_alvo_em_linha_de_ataque(self):
        if self.personagem is None:
            return None

        # A direção da investida nasce da última direção horizontal válida.
        dx = getattr(self.personagem, "ultimo_direcao_x", 0) or 0
        dy = getattr(self.personagem, "ultimo_direcao_y", 0) or 0

        # Prioriza a direção visual quando disponível. O bandido possui ataque
        # horizontal nos assets atuais, mas mantemos o cálculo vetorial para não
        # acoplar a regra a um único eixo futuramente.
        alvo_atual = self.entidade_alvo
        if alvo_atual is not None and getattr(alvo_atual, "vida", 0) > 0:
            dx_alvo = alvo_atual.x - self.personagem.x
            dy_alvo = alvo_atual.y - self.personagem.y
            if abs(dx_alvo) > 1 or abs(dy_alvo) > 1:
                if abs(dx_alvo) >= abs(dy_alvo):
                    dx = -1.0 if dx_alvo < 0 else 1.0
                    dy = 0.0
                else:
                    dx = 0.0
                    dy = -1.0 if dy_alvo < 0 else 1.0

        if dx == 0 and dy == 0:
            dx = -1.0 if getattr(self.personagem.animacoes, "flip", False) else 1.0

        tamanho = hypot(dx, dy) or 1.0
        dx /= tamanho
        dy /= tamanho

        indice = getattr(self.cenario_principal, "indice_espacial", None)
        if indice is not None:
            candidatos = indice.consultar_raio(
                self.personagem.x,
                self.personagem.y,
                self.RAIO_DETECCAO_INIMIGO,
                grupos=("personagens", "hostis"),
            )
        else:
            candidatos = [
                item["entidade"]
                for item in self.cenario_principal.entidades
                if item["grupo"] in ("personagens", "hostis")
            ]

        registro_personagem = self.cenario_principal.obter_entidade(self.personagem)
        config_personagem = obter_config(self.personagem.nome)
        faccao = (
            registro_personagem.get("faccao")
            if registro_personagem is not None
            and registro_personagem.get("faccao") is not None
            else config_personagem.get("faccao")
        )

        melhor = None
        melhor_projecao = None

        for candidato in candidatos:
            if candidato is self.personagem or getattr(candidato, "vida", 0) <= 0:
                continue
            registro = self.cenario_principal.obter_entidade(candidato)
            if registro is None or registro.get("faccao") == faccao:
                continue
            if faccao is None and registro.get("faccao") is None:
                continue

            vetor_x = candidato.x - self.personagem.x
            vetor_y = candidato.y - self.personagem.y
            projecao = vetor_x * dx + vetor_y * dy
            if projecao <= 8.0 or projecao > self.RAIO_DETECCAO_INIMIGO:
                continue

            lateral = abs(vetor_x * dy - vetor_y * dx)
            if lateral > self.LARGURA_LINHA_ATAQUE:
                continue

            # Obstáculo entre bandido e alvo cancela a investida em linha.
            if self.navegacao.linha_bloqueada_por_obstaculos(
                self.personagem.x,
                self.personagem.y,
                candidato.x,
                candidato.y,
            ):
                continue

            if melhor_projecao is None or projecao < melhor_projecao:
                melhor = candidato
                melhor_projecao = projecao

        return melhor

    def _iniciar_investida(self, alvo):
        if self.investida_ativa:
            return

        dx = alvo.x - self.personagem.x
        dy = alvo.y - self.personagem.y
        tamanho = hypot(dx, dy) or 1.0
        self.investida_dx = dx / tamanho
        self.investida_dy = dy / tamanho

        if hasattr(self.personagem.animacoes, "definir_por_direcao"):
            self.personagem.animacoes.definir_por_direcao(
                "atacando", dx if abs(dx) >= abs(dy) else self.investida_dx
            )
            self.personagem.animacoes.reset()
        else:
            self._iniciar_ataque()

        self.investida_ativa = True
        self.investida_decorrido = 0.0
        self.investida_x_inicial = self.personagem.x
        self.investida_y_inicial = self.personagem.y
        self.investida_distancia_percorrida = 0.0
        self.inimigos_atingidos_na_investida.clear()
        self.alvo_golpe_confirmado = alvo
        self.personagem.destino_x = self.personagem.x
        self.personagem.destino_y = self.personagem.y

    def _executar_investida(self, dt):
        self.investida_decorrido += dt
        passo = self.VELOCIDADE_INVESTIDA * dt
        if passo <= 0:
            return

        distancia_restante = (
            self.DISTANCIA_MAXIMA_INVESTIDA - self.investida_distancia_percorrida
        )
        passo = min(passo, max(0.0, distancia_restante))

        x_anterior = self.personagem.x
        y_anterior = self.personagem.y
        novo_x = x_anterior + self.investida_dx * passo
        novo_y = y_anterior + self.investida_dy * passo

        # Investida é linear. Ela nunca atravessa um obstáculo do mapa.
        if not self.navegacao.pode_andar(novo_x, novo_y, self.personagem.altura):
            self.investida_decorrido = max(
                self.investida_decorrido, self.TEMPO_MAXIMO_INVESTIDA
            )
            self._aguardar_fim_animacao_ataque()
            return
        if self.navegacao.linha_bloqueada_por_obstaculos(
            x_anterior,
            y_anterior,
            novo_x,
            novo_y,
        ):
            self.investida_decorrido = max(
                self.investida_decorrido, self.TEMPO_MAXIMO_INVESTIDA
            )
            self._aguardar_fim_animacao_ataque()
            return

        self.personagem.x = novo_x
        self.personagem.y = novo_y
        self.investida_distancia_percorrida += passo
        indice = getattr(self.cenario_principal, "indice_espacial", None)
        atualizar_indice = (
            getattr(indice, "atualizar", None) if indice is not None else None
        )
        if callable(atualizar_indice):
            atualizar_indice(self.personagem)

        if self.navegacao.linha_bloqueada_por_obstaculos(
            x_anterior,
            y_anterior,
            novo_x,
            novo_y,
        ):
            self._finalizar_investida()
            return

        # Acerta qualquer inimigo que a faixa de ataque atravesse, não apenas o
        # alvo originalmente adquirido. Isso torna a investida realmente em linha.
        self._causar_dano_na_faixa(x_anterior, y_anterior, novo_x, novo_y)

        terminou_deslocamento = (
            self.investida_distancia_percorrida
            >= self.DISTANCIA_MAXIMA_INVESTIDA - 0.001
            or self.investida_decorrido >= self.TEMPO_MAXIMO_INVESTIDA
        )

        # A investida física pode terminar antes da animação. Mesmo assim,
        # o estado de ataque permanece bloqueado até o último frame do golpe.
        # Isso impede que corrida, defesa ou troca de alvo sobrescrevam a
        # animação no meio da investida.
        animacao = getattr(self.personagem.animacoes, "animacao_atual", None)
        terminou_animacao = bool(
            animacao is None or getattr(animacao, "progresso", 1.0) >= 1.0
        )

        if terminou_deslocamento and terminou_animacao:
            self._finalizar_investida()

    def _causar_dano_na_faixa(self, x1, y1, x2, y2):
        indice = getattr(self.cenario_principal, "indice_espacial", None)
        if indice is not None:
            candidatos = indice.consultar_raio(
                (x1 + x2) / 2.0,
                (y1 + y2) / 2.0,
                max(48.0, self.LARGURA_LINHA_ATAQUE + 24.0),
                grupos=("personagens", "hostis"),
            )
        else:
            candidatos = [
                item["entidade"]
                for item in self.cenario_principal.entidades
                if item["grupo"] in ("personagens", "hostis")
            ]

        registro_personagem = self.cenario_principal.obter_entidade(self.personagem)
        faccao = registro_personagem.get("faccao") if registro_personagem else None

        dx = x2 - x1
        dy = y2 - y1
        comprimento = hypot(dx, dy) or 1.0
        ux = dx / comprimento
        uy = dy / comprimento

        for candidato in candidatos:
            if (
                candidato is self.personagem
                or id(candidato) in self.inimigos_atingidos_na_investida
            ):
                continue
            if getattr(candidato, "vida", 0) <= 0:
                continue

            registro = self.cenario_principal.obter_entidade(candidato)
            if registro is None or registro.get("faccao") == faccao:
                continue
            if faccao is None and registro.get("faccao") is None:
                continue

            vx = candidato.x - x1
            vy = candidato.y - y1
            projecao = vx * ux + vy * uy
            if projecao < -12 or projecao > comprimento + 12:
                continue
            lateral = abs(vx * uy - vy * ux)
            if lateral > self.LARGURA_LINHA_ATAQUE:
                continue

            self._causar_dano_investida(candidato)
            self.inimigos_atingidos_na_investida.add(id(candidato))

    def _causar_dano_investida(self, alvo):
        # A investida adiciona exatamente 1 de dano ao golpe que o alvo já
        # receberia do ataque básico do bandido.
        dano = max(
            1,
            int(getattr(self.personagem, "ataque", 0))
            - int(getattr(alvo, "defesa", 0)),
        )
        dano += 1

        vida_anterior = getattr(alvo, "vida", 0)
        alvo.vida = max(0, vida_anterior - dano)
        dano_aplicado = max(0, vida_anterior - alvo.vida)
        alvo.tempo_barra_vida = getattr(alvo, "TEMPO_EXIBIR_BARRA_VIDA", 3.0)
        if dano_aplicado > 0:
            registrar_dano = getattr(
                self.cenario_principal, "registrar_dano_visual", None
            )
            if registrar_dano is not None:
                registrar_dano(alvo, dano_aplicado)

        ctrl = self.cenario_principal.controladores.get(alvo)
        if ctrl is not None:
            atacar = ctrl.get("acoes", {}).get("atacar")
            if atacar is not None:
                atacar["usecase"].registrar_atacante(self.personagem)
                atacar["usecase"].iniciar(self.personagem, alvo)

        self.chamar_defensores.executar(
            alvo,
            self.personagem,
            self.cenario_principal.obter_entidade(alvo).get("faccao")
            if self.cenario_principal.obter_entidade(alvo)
            else None,
        )

    def _aguardar_fim_animacao_ataque(self):
        animacao = getattr(self.personagem.animacoes, "animacao_atual", None)
        if animacao is None or getattr(animacao, "progresso", 1.0) >= 1.0:
            self._finalizar_investida()

    def _finalizar_investida(self):
        self.investida_ativa = False
        self.investida_decorrido = 0.0
        self.investida_distancia_percorrida = 0.0
        self.alvo_golpe_confirmado = None
        self.personagem.destino_x = self.personagem.x
        self.personagem.destino_y = self.personagem.y
        self.personagem.animacoes.definir("ocioso", flip=self.personagem.animacoes.flip)
        self.tempo_apos_golpe = self.INTERVALO_APOS_GOLPE

    def _apos_causar_dano(self):
        # Mantido para compatibilidade com o contrato da classe base. O dano
        # real da investida é aplicado pela própria faixa de deslocamento.
        self.tempo_apos_golpe = self.INTERVALO_APOS_GOLPE
