from math import hypot

from domains.arvore.maquina_estado import EstadoArvore
from domains.personagem.maquina_estado import EstadoAldeao
from utils.config import TILE_SIZE


class CortarArvoreUseCase:
    VELOCIDADE = 110
    DISTANCIA_PARADA = 18
    TEMPO_OBTENDO = 4.0
    RAIO_BUSCA_ARVORE_TILES = 4

    def __init__(self, cenario_principal):
        self.cenario_principal = cenario_principal
        self.guardar_recurso_x = 550
        self.guardar_recurso_y = 275

        self.entidade_alvo = None

        self.tempo = 0.0
        self.flip = False
        self.ultima_posicao_corte_x = None
        self.ultima_posicao_corte_y = None
        # Quando uma árvore termina, a ação pode precisar esperar alguns
        # instantes até encontrar outra disponível. Mantemos a ação viva para
        # não devolver o aldeão ao comportamento ocioso antes da troca.
        self._tempo_proxima_arvore = 0.0
        self._intervalo_busca_proxima_arvore = 0.25

    def iniciar(self, arvore, personagem, manual=False):
        if not self._arvore_disponivel(arvore):
            self.entidade_alvo = None
            return False

        self.entidade_alvo = arvore
        self.personagem = personagem
        self._tempo_proxima_arvore = 0.0

        # Este ponto é a referência para procurar a próxima árvore.
        self.ultima_posicao_corte_x = arvore.x
        self.ultima_posicao_corte_y = arvore.y

        # A própria ação de corte também redefine o raio de movimentação livre.
        personagem.definir_base_movimento(arvore.x, arvore.y)

        self.tempo = 0.0

        self.flip = arvore.x < self.personagem.x

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_MACHADO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_MACHADO

        return True

    def cancelar(self):
        self.entidade_alvo = None
        self.personagem = None
        self._tempo_proxima_arvore = 0.0

    def executar(self, dt):
        if self.entidade_alvo is None:
            return

        self._tempo_proxima_arvore = max(0.0, self._tempo_proxima_arvore - dt)

        # Quem já está levando madeira precisa concluir a entrega mesmo que
        # a árvore de origem tenha acabado. A troca para a próxima árvore
        # acontece depois que o recurso é entregue.
        if self.personagem.animacoes.maquina.entregando_madeira():
            self._entregar(dt)
            return

        if self.personagem.animacoes.maquina.cortando_arvore():
            self._obter(dt)
            return

        # A árvore pode acabar enquanto o aldeão ainda está chegando.
        if not self._arvore_disponivel(self.entidade_alvo):
            if self._tentar_trocar_arvore():
                return
            self._aguardar_nova_arvore()
            return

        self._andar(dt)

    # --------------------------------------------------------

    def _arvore_disponivel(self, arvore):
        if arvore is None:
            return False

        if getattr(arvore, "madeira", 0) <= 0:
            return False

        return getattr(arvore.animacoes, "estado", None) != EstadoArvore.CORTADA

    def _buscar_arvore_proxima(self, origem_x=None, origem_y=None, excluir=None):
        if origem_x is None:
            origem_x = self.ultima_posicao_corte_x
        if origem_y is None:
            origem_y = self.ultima_posicao_corte_y

        if origem_x is None or origem_y is None:
            return None

        raio = self.RAIO_BUSCA_ARVORE_TILES * TILE_SIZE
        melhor = None
        melhor_distancia = None

        indice = getattr(self.cenario_principal, "indice_espacial", None)
        if indice is not None:
            arvores = indice.consultar_raio(
                origem_x,
                origem_y,
                raio,
                grupos=("arvores",),
            )
            # A árvore é uma entidade estática, mas o índice é uma otimização.
            # Nunca deixe a manutenção do índice impedir a retomada da coleta.
            # Se ele não devolver candidatos, fazemos fallback para a coleção
            # oficial do cenário e mantemos a mesma filtragem por distância.
            if not arvores:
                arvores = getattr(self.cenario_principal, "arvores", ())
        else:
            arvores = getattr(self.cenario_principal, "arvores", ())
        metricas = getattr(self.cenario_principal, "metricas_desempenho", None)
        if metricas is not None:
            metricas.contar("buscas_arvore")
        for arvore in arvores:
            if arvore is excluir or arvore is self.entidade_alvo:
                continue
            if not self._arvore_disponivel(arvore):
                continue

            distancia = hypot(arvore.x - origem_x, arvore.y - origem_y)
            if distancia > raio:
                continue

            if melhor is None or distancia < melhor_distancia:
                melhor = arvore
                melhor_distancia = distancia

        return melhor

    def _procurar_arvore_proxima(self):
        arvore_atual = self.entidade_alvo
        arvore = self._buscar_arvore_proxima(excluir=arvore_atual)

        if arvore is None:
            return False

        return self.iniciar(arvore, self.personagem)

    def _tentar_trocar_arvore(self):
        if self._tempo_proxima_arvore > 0.0:
            return False

        self._tempo_proxima_arvore = self._intervalo_busca_proxima_arvore
        return self._procurar_arvore_proxima()

    def _aguardar_nova_arvore(self):
        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.OCIOSO

        self.personagem.destino_x = self.personagem.x
        self.personagem.destino_y = self.personagem.y

    def _parar_sem_arvore(self):
        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.OCIOSO

        self.personagem.destino_x = self.personagem.x
        self.personagem.destino_y = self.personagem.y
        self.entidade_alvo = None

    # --------------------------------------------------------

    def _andar(self, dt):
        if not self._arvore_disponivel(self.entidade_alvo):
            if self._tentar_trocar_arvore():
                return
            self._aguardar_nova_arvore()
            return

        destino_x, destino_y = self._obter_destino_corte()

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            self.tempo = 0.0

            if self.flip:
                self.personagem.animacoes.estado = EstadoAldeao.USANDO_MACHADO_FLIP
            else:
                self.personagem.animacoes.estado = EstadoAldeao.USANDO_MACHADO

            return

        if distancia > 0:
            self.personagem.destino_x = destino_x
            self.personagem.destino_y = destino_y

            self.cenario_principal.mover_personagem.executar(
                personagem=self.personagem,
                navegacao=self.cenario_principal.navegacao,
                velocidade=self.VELOCIDADE,
                estado_correndo=EstadoAldeao.CORRENDO_MACHADO,
                estado_correndo_flip=EstadoAldeao.CORRENDO_MACHADO_FLIP,
                estado_parado=EstadoAldeao.OCIOSO,
                estado_parado_flip=EstadoAldeao.OCIOSO_FLIP,
                dt=dt,
            )

    def _obter_destino_corte(self):
        """Obtém a posição de trabalho sem depender do renderer.

        Em determinados momentos do ciclo do jogo, principalmente logo após
        a troca automática para uma nova árvore, a entidade ainda pode não
        ter recebido um `corpo_rect`. A lógica de domínio não deve depender
        da renderização para conseguir navegar até a árvore.
        """
        rect = getattr(self.entidade_alvo, "corpo_rect", None)

        if rect is not None:
            if self.flip:
                destino_x = rect.right - 5
            else:
                destino_x = rect.left - 1
            destino_y = rect.bottom - 25
            return destino_x, destino_y

        # Fallback baseado na posição lógica da árvore. Mantemos as mesmas
        # dimensões usadas pelo harness/renderizador para que a posição de
        # corte continue consistente mesmo antes do primeiro render.
        metade_largura = 32
        metade_altura = 48

        if self.flip:
            destino_x = self.entidade_alvo.x + metade_largura - 5
        else:
            destino_x = self.entidade_alvo.x - metade_largura - 1

        destino_y = self.entidade_alvo.y + metade_altura - 25
        return destino_x, destino_y

    # --------------------------------------------------------

    def _obter(self, dt):
        if not self._arvore_disponivel(self.entidade_alvo):
            if self._tentar_trocar_arvore():
                return
            self._aguardar_nova_arvore()
            return

        self.tempo += dt

        if self.tempo < self.TEMPO_OBTENDO:
            return

        self.flip = self.guardar_recurso_x < self.personagem.x
        self.entidade_alvo.obter_madeira()

        if self.flip:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_MADEIRA_FLIP
        else:
            self.personagem.animacoes.estado = EstadoAldeao.CORRENDO_MADEIRA

    def _entregar(self, dt):
        arvore_alvo = self.entidade_alvo

        destino_x = self.guardar_recurso_x - 40
        destino_y = self.guardar_recurso_y + 150

        dx = destino_x - self.personagem.x
        dy = destino_y - self.personagem.y

        distancia = hypot(dx, dy)

        if distancia <= self.DISTANCIA_PARADA:
            if self.flip:
                self.personagem.animacoes.estado = EstadoAldeao.OCIOSO_FLIP
            else:
                self.personagem.animacoes.estado = EstadoAldeao.OCIOSO

            OFFSET = 40

            if self.flip:
                recurso_x = self.personagem.x - OFFSET
            else:
                recurso_x = self.personagem.x + OFFSET

            recurso_y = self.personagem.y

            self.cenario_principal.carregar_entidade("madeira", recurso_x, recurso_y)
            self.cenario_principal.adicionar_estoque("madeira", 1)

            # Se a árvore ainda possui madeira, continua nela.
            # Se acabou, procura automaticamente uma nova árvore disponível
            # próxima ao último ponto de corte. Caso ela ainda não esteja
            # disponível, mantemos a ação viva e tentamos novamente em breve.
            if self._arvore_disponivel(arvore_alvo):
                self.iniciar(arvore_alvo, self.personagem)
            elif not self._procurar_arvore_proxima():
                self._aguardar_nova_arvore()

            return

        self.personagem.destino_x = destino_x
        self.personagem.destino_y = destino_y

        self.cenario_principal.mover_personagem.executar(
            personagem=self.personagem,
            navegacao=self.cenario_principal.navegacao,
            velocidade=self.VELOCIDADE,
            estado_correndo=EstadoAldeao.CORRENDO_MADEIRA,
            estado_correndo_flip=EstadoAldeao.CORRENDO_MADEIRA_FLIP,
            estado_parado=EstadoAldeao.OCIOSO,
            estado_parado_flip=EstadoAldeao.OCIOSO_FLIP,
            dt=dt,
        )
