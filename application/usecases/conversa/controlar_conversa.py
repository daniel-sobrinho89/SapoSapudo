from contextlib import suppress
from math import hypot

from application.usecases.aldeao.construir_casa import ConstruirCasaUseCase
from application.usecases.aldeao.recolher_noite import RecolherBernardoUseCase
from application.usecases.personagem.mover import MoverPersonagemUseCase
from application.usecases.sapudo.evolucao import EvolucaoSapudoUseCase
from domains.interacao_item import ItemInterativo
from utils.config import TILE_SIZE


class ControlarConversaUseCase:
    CASA_MADEIRA_NECESSARIA = 14

    ESTADOS = (
        "inicial",
        "aguardando_bandidos",
        "dialogo_bandidos",
        "combate_bandidos",
        "machado_com_sapudo",
        "bernardo_trabalhando",
        "casa_construindo",
        "missao_planalto_cobras",
        "aguardando_roubao",
        "dialogo_roubao",
        "roubao_retornando",
        "martelo_com_sapudo",
        "missao_planalto_concluida",
        "casa_pronta",
        "casa_visitada",
    )

    def __init__(self, cenario):
        self.cenario = cenario
        self.aberta = False
        self.estado = "inicial"
        self.bernardo = None
        self.machado = None
        self.bandidos = []
        self.bandidos_derrotados = 0
        self.ultimo_bandido_morto = None
        self._machado_spawnado = False
        self._bandidos_mortos_registrados = set()
        self._dialogo_bandidos_iniciado = False
        self._combat_started = False
        self.renderer = None
        self.inventario = {"machado": False, "martelo": False}
        self.recolher_bernardo = RecolherBernardoUseCase(
            cenario, self._casa_bernardo, self._arvore_para_noite
        )
        self.martelo_recebido_por_bernardo = False
        self.raio_interacao = 88
        self.mensagem_proximidade = None
        self.evolucao = EvolucaoSapudoUseCase()
        self.construir_casa = ConstruirCasaUseCase(cenario)
        self.evolucao_pendente = False
        self.cobras_missao = []
        self.cobras_derrotadas = 0
        self.caverna_missao = None
        self.martelo = None
        self.casa_construindo = None
        self.casa_posicao = None
        self.casa_madeira_entregue = 0
        self.casa_madeira_para_transportar = 0
        self.casa_ponto_entrega = None
        self.casa_fase = None
        self._dialogo_missao_planalto_iniciado = False
        self._dialogo_martelo_pronto = False
        self.roubao = None
        self._roubao_retorno_iniciado = False
        self._roubao_dialogo_iniciado = False
        self._roubao_saida_ativa = False
        self._roubao_saida_ativa = False
        self._movimento_roubao = MoverPersonagemUseCase()

    def definir_renderer(self, renderer):
        self.renderer = renderer

    def _casa_bernardo_disponivel_para_entrada(self):
        """A casa de Bernardo permite entrada somente entre 18:00 e antes de 05:00."""
        hora = float(self.cenario.ciclo_dia_noite.hora) % 24.0
        return hora >= 18.0 or hora < 5.0

    @property
    def roubao_controlado_pela_quest(self):
        """Roubão não pode ser processado pela IA genérica durante a missão."""
        if self.roubao is None:
            return False
        return self._roubao_saida_ativa or self.estado in {
            "aguardando_roubao",
            "dialogo_roubao",
            "roubao_retornando",
            "roubao_saida",
            "martelo_com_sapudo",
        }

    @property
    def bernardo_ocupado_pela_quest(self):
        return self.estado in {
            "inicial",
            "aguardando_bandidos",
            "dialogo_bandidos",
            "combate_bandidos",
            "machado_com_sapudo",
            "bernardo_trabalhando",
            "casa_construindo",
            "aguardando_roubao",
            "dialogo_roubao",
            "roubao_retornando",
            "roubao_saida",
            "missao_planalto_cobras",
            "martelo_com_sapudo",
            "missao_planalto_concluida",
        }

    def pode_receber_xp_missao(self, missao_id):
        return missao_id in {"missao_bandido_bernardo", "missao_cobras_planalto"}

    def registrar_bernardo(self, personagem):
        self.bernardo = personagem
        if getattr(personagem, "posicao_inicial", None) is None:
            personagem.posicao_inicial = (personagem.x, personagem.y)
        self.recolher_bernardo.destino_inicial = personagem.posicao_inicial

    def _casa_palha_vermelha(self):
        """Retorna a casa dos bandidos definida no mundo narrativo."""
        for construcao in getattr(self.cenario, "construcoes_hostis", ()):
            if getattr(construcao, "nome", None) == "casa_palha_vermelha":
                return construcao
        for construcao in getattr(self.cenario, "construcoes", ()):
            if getattr(construcao, "nome", None) == "casa_palha_vermelha":
                return construcao
        return None

    def atualizar(self, dt):
        if self.bernardo is None:
            return

        # Diálogo aberto é uma barreira real para os fluxos de missão:
        # Bernardo, Roubão e qualquer outra rotina controlada pela conversa
        # não podem continuar alterando posição enquanto a UI está aberta.
        # O renderer da conversa continua respondendo aos comandos do jogador,
        # mas o mundo permanece congelado até o diálogo ser encerrado.
        if self.aberta:
            return

        # O recolhimento noturno tem prioridade sobre o trabalho. Enquanto
        # Bernardo estiver indo dormir ou já estiver escondido, nenhum fluxo
        # de coleta/construção pode mover ou animar o personagem.
        self.recolher_bernardo.atualizar(
            dt, self.cenario.ciclo_dia_noite.hora, self.bernardo
        )
        if self.recolher_bernardo.dormindo_ou_recolhendo:
            return

        # O trabalho da casa é independente da conversa. Bernardo não perde
        # a atividade de corte/transporte só porque Sapudo entregou o martelo
        # e abriu um diálogo.
        self._atualizar_construcao_bernardo(dt)

        # A saída de Roubão é um subfluxo independente do estado global. Isso
        # permite que Sapudo pegue o martelo enquanto Roubão continua correndo
        # até a caverna sem voltar à IA hostil.
        if self._roubao_saida_ativa:
            if not self.aberta:
                self._atualizar_saida_roubao(dt)
            return

        if self.aberta:
            return

        if self.estado == "combate_bandidos":
            self._atualizar_combate_bandidos()
            return

        if self.estado == "aguardando_roubao":
            self._atualizar_encontro_roubao()
            return

        if self.estado == "roubao_retornando":
            self._atualizar_retorno_roubao(dt)
            return

        if self.estado == "roubao_saida":
            self._atualizar_saida_roubao(dt)
            return

        if self.estado == "missao_planalto_cobras":
            self._atualizar_missao_cobras()
            return

    def tecla_interagir(self):
        if self.evolucao_pendente:
            return True
        if self.aberta:
            self.renderer.avancar()
            self.aberta = self.renderer.aberta
            return True

        sapudo = self._sapudo()
        if sapudo is None:
            return False

        # A casa concluída por Bernardo continua sendo um ponto de interação
        # mesmo quando Bernardo já foi recolhido para dormir e, portanto,
        # está invisível. O bloqueio de Bernardo vale para as demais
        # interações narrativas, não para a casa dele.
        casa = self._casa_bernardo()
        if (
            self.estado in ("casa_pronta", "casa_visitada")
            and casa is not None
            and self._perto(sapudo, casa.x, casa.y, raio=105)
        ):
            if self._casa_bernardo_disponivel_para_entrada():
                iniciar_descanso = getattr(
                    self.cenario, "iniciar_descanso_sapudo", None
                )
                if callable(iniciar_descanso) and iniciar_descanso():
                    self.estado = "casa_visitada"
                    self.mensagem_proximidade = None
                    return True
            return True

        if self.bernardo is not None and not getattr(self.bernardo, "visivel", True):
            return False

        casa_bandidos = self._casa_palha_vermelha()
        if casa_bandidos is not None and self._perto(
            sapudo, casa_bandidos.x, casa_bandidos.y, raio=125
        ):
            if self.estado == "inicial":
                self._dialogo_casa_sem_ninguem()
                return True
            if self.estado == "aguardando_bandidos" and not self.bandidos:
                self._dialogo_casa_bandidos_missao()
                return True

        if (
            self.machado is not None
            and not self.machado.coletado
            and self._perto(sapudo, self.machado.x, self.machado.y)
        ):
            self.machado.coletado = True
            self.inventario["machado"] = True
            self.estado = "machado_com_sapudo"
            return True

        if (
            self.martelo is not None
            and not self.martelo.coletado
            and self._perto(sapudo, self.martelo.x, self.martelo.y)
        ):
            self.martelo.coletado = True
            self.inventario["martelo"] = True
            self.estado = "martelo_com_sapudo"
            return True

        if (
            self.estado == "martelo_com_sapudo"
            and self.bernardo is not None
            and self._perto(sapudo, self.bernardo.x, self.bernardo.y)
        ):
            self._conversar_martelo()
            return True

        if self.bernardo is not None and self._perto(
            sapudo, self.bernardo.x, self.bernardo.y
        ):
            self._conversar_com_bernardo()
            return True

        return False

    def escolher_evolucao(self, atributo):
        if not self.evolucao_pendente:
            return False
        sapudo = self._sapudo()
        if sapudo is None:
            return False
        aplicada = self.evolucao.aplicar_ponto(sapudo, atributo)
        if aplicada and sapudo.pontos_evolucao <= 0:
            self.evolucao_pendente = False

        return aplicada

    def cancelar_dialogo(self):
        if not self.aberta:
            return False
        self.aberta = False
        if self.renderer is not None:
            self.renderer.fechar()
        if self.estado == "dialogo_bandidos":
            self.estado = "aguardando_bandidos"
            self._dialogo_bandidos_iniciado = False
        return True

    def prompt(self):
        if self.aberta:
            return None
        sapudo = self._sapudo()
        if sapudo is None:
            return None

        # A casa finalizada por Bernardo deve continuar mostrando a opção de
        # entrada durante a janela noturna, mesmo com Bernardo recolhido e
        # invisível. Esta verificação precisa acontecer antes do bloqueio
        # geral das interações dependentes de Bernardo.
        casa = self._casa_bernardo()
        if (
            self.estado in ("casa_pronta", "casa_visitada")
            and casa is not None
            and self._perto(sapudo, casa.x, casa.y, raio=105)
            and self._casa_bernardo_disponivel_para_entrada()
        ):
            return "[E] Entrar / descansar"

        if self.bernardo is not None and not getattr(self.bernardo, "visivel", True):
            return None

        casa_bandidos = self._casa_palha_vermelha()
        if (
            casa_bandidos is not None
            and self._perto(sapudo, casa_bandidos.x, casa_bandidos.y, raio=125)
            and self.estado in {"inicial", "aguardando_bandidos"}
            and not self.bandidos
        ):
            return "[E] Interagir com a casa"

        if (
            self.machado is not None
            and not self.machado.coletado
            and self._perto(sapudo, self.machado.x, self.machado.y)
        ):
            return "[E] Pegar machado"
        if (
            self.martelo is not None
            and not self.martelo.coletado
            and self._perto(sapudo, self.martelo.x, self.martelo.y)
        ):
            return "[E] Pegar martelo"
        if (
            self.estado == "martelo_com_sapudo"
            and self.bernardo is not None
            and self._perto(sapudo, self.bernardo.x, self.bernardo.y)
        ):
            return "[E] Entregar martelo a Bernardo"

        if self.bernardo is not None and self._perto(
            sapudo, self.bernardo.x, self.bernardo.y
        ):
            return "[E] Conversar com Bernardo"
        return None

    def _orientar_participantes_com_bernardo(self):
        bernardo = self.bernardo
        sapudo = self._sapudo()
        if bernardo is None or sapudo is None:
            return

        bernardo.animacoes.definir_por_direcao("ocioso", sapudo.x - bernardo.x)
        sapudo.animacoes.definir_por_direcao("ocioso", bernardo.x - sapudo.x)

    def _conversar_com_bernardo(self):
        self._orientar_participantes_com_bernardo()
        if (
            self.estado in {"aguardando_bandidos", "combate_bandidos"}
            and self._ha_bandidos_derrotados()
        ):
            self._repor_bandidos_para_missao()
            self.estado = "aguardando_bandidos"
            self._dialogo_bandidos_iniciado = False
            self._combat_started = False
            return

        if self.estado == "inicial":
            self._dialogo(
                [
                    (
                        "aldeao",
                        "Bernardo",
                        "Olá senhor, senhora, jovem, enfim, não dá bem para saber quem é atrás desta armadura!",
                    ),
                    (
                        "aldeao",
                        "Bernardo",
                        "Pode simplesmente ser um pé de feijão que criou vida e agora anda por ai com esta armadura!",
                    ),
                    (
                        "aldeao",
                        "Bernardo",
                        "Então te chamarei de sapo, um sapo grande, Sapudo!",
                    ),
                    ("sapudo", "Sapudo", "Não sei se sapos podem falar, mas que seja!"),
                    (
                        "aldeao",
                        "Bernardo",
                        "Então Sapudo, temos um grande problema por estes lados, tem um urso que toda noite sai descontroladamente a atacar!",
                    ),
                    (
                        "aldeao",
                        "Bernardo",
                        "Eu não tenho muito problema com ele, pois simplesmente subo em uma daquelas árvores ali e passo a noite nela!",
                    ),
                    (
                        "aldeao",
                        "Bernardo",
                        "Mas seria bom se tivesse uma casa, uma linda casa de palha para poder me abrigar!",
                    ),
                    (
                        "aldeao",
                        "Bernardo",
                        "Se encontrar algum machado, eu poderei cortar algumas destas lindas árvores e começar o serviço!",
                    ),
                    (
                        "sapudo",
                        "Sapudo",
                        "Bom, se eu encontrar o machado, espero que me abrigue na casa também!",
                    ),
                    (
                        "sapudo",
                        "Sapudo",
                        "Irei em busca de algum, pois sei que ursos não conseguem asoprar e sem dúvidas não derrubará esta linda casa!",
                    ),
                    ("aldeao", "Bernardo", "Boa sorte Sapudo!"),
                ],
                self._após_dialogo_machado,
            )
            return

        if self.estado == "machado_com_sapudo":
            self._dialogo(
                [
                    ("aldeao", "Bernardo", "Aqui está! Um lindo machado!"),
                    (
                        "sapudo",
                        "Sapudo",
                        "Então ao trabalho! O Sol deve se por em breve!",
                    ),
                    ("aldeao", "Bernardo", "Já estou trabalhando! Estou trabalhando!"),
                ],
                self._entregar_machado,
            )
            return

        if self.estado == "casa_pronta":
            self._dialogo(
                [
                    (
                        "aldeao",
                        "Bernardo",
                        "É isto uma linda casa de palha! Ainda precisa de alguma decoração, mas por hora está muito boa!",
                    ),
                    (
                        "aldeao",
                        "Bernardo",
                        "Você também pode descansar aqui quando precisar!",
                    ),
                    ("sapudo", "Sapudo", "Não serei sobremesa de urso esta noite!"),
                ],
                lambda: None,
            )
            return

        self._dialogo(
            [
                (
                    "aldeao",
                    "Bernardo",
                    "A floresta está logo ali! Siga para sua aventura!",
                )
            ],
            lambda: None,
        )

    def _após_dialogo_machado(self):
        self.bandidos = []
        self.bandidos_derrotados = 0
        self.ultimo_bandido_morto = None
        self._dialogo_bandidos_iniciado = False
        self._combat_started = False
        self.estado = "aguardando_bandidos"

    def _dialogo_casa_sem_ninguem(self):
        self._dialogo(
            [
                ("bandido", "Bandido", "Não tem ninguém em casa, vá embora."),
            ],
            lambda: None,
        )

    def _dialogo_casa_bandidos_missao(self):
        self._dialogo(
            [
                ("bandido", "Bandido", "Não tem ninguém em casa, vá embora."),
                (
                    "sapudo",
                    "Sapudo",
                    "Pois então seu ninguém, eu sinto que pode ter algum machado por aqui, e preciso dele!",
                ),
                (
                    "bandido",
                    "Bandido",
                    "Certo seu linguarudo! Tem sim machado e em breve também seu lindo escudo!",
                ),
            ],
            self._revelar_bandidos_e_iniciar_combate,
        )

    def _revelar_bandidos_e_iniciar_combate(self):
        self._repor_bandidos_para_missao()
        self.estado = "combate_bandidos"
        self._dialogo_bandidos_iniciado = False
        self._combat_started = True
        sapudo = self._sapudo()
        if sapudo is None:
            return

        for bandido in self.bandidos:
            ctrl = self.cenario.controladores.get(bandido)
            atacar = ctrl.get("acoes", {}).get("atacar") if ctrl else None
            if atacar is not None:
                iniciar = getattr(atacar["usecase"], "iniciar", None)
                if callable(iniciar):
                    iniciar(sapudo, bandido)

    def _ha_bandidos_derrotados(self):
        return any(getattr(bandido, "vida", 0) <= 0 for bandido in self.bandidos)

    def _repor_bandidos_para_missao(self):
        """Cria os dois bandidos narrativos do Vale dos Ossos."""
        bandidos_atuais = list(self.bandidos)
        recomposicao = []

        if not hasattr(self, "_posicoes_bandidos_missao"):
            self._posicoes_bandidos_missao = []
            casa = self._casa_palha_vermelha()
            if casa is not None:
                cx, cy = casa.x, casa.y
                self._posicoes_bandidos_missao = [
                    (cx - 150, cy - 55, getattr(casa, "altura", 0)),
                    (cx + 150, cy - 55, getattr(casa, "altura", 0)),
                ]
            else:
                world_context = getattr(self.cenario, "world_context", None)
                if world_context is not None:
                    try:
                        self._posicoes_bandidos_missao = [
                            (spawn.posicao.x, spawn.posicao.y, spawn.posicao.altura)
                            for spawn in world_context.spawn_system.obter_spawns_tipo(
                                "bandido"
                            )
                            if "narrativa" in spawn.tags
                        ]
                    except AttributeError:
                        self._posicoes_bandidos_missao = []

        vivos = [e for e in bandidos_atuais if getattr(e, "vida", 0) > 0]

        for bandido in vivos:
            self._resetar_estado_bandido(bandido)
            bandido.xp_recompensa = 34
            bandido.xp_missao_id = "missao_bandido_bernardo"
            bandido.xp_recompensada = False
            recomposicao.append(bandido)

        while len(recomposicao) < 2:
            indice = len(recomposicao)
            if indice < len(self._posicoes_bandidos_missao):
                x, y, altura = self._posicoes_bandidos_missao[indice]
                novo = self.cenario.carregar_entidade("bandido", x, y)
            else:
                modelo = next(
                    (
                        e
                        for e in bandidos_atuais
                        if e not in vivos and getattr(e, "nome", None) == "bandido"
                    ),
                    None,
                )
                if modelo is None:
                    break
                x = getattr(modelo, "base_x", modelo.x)
                y = getattr(modelo, "base_y", modelo.y)
                novo = self.cenario.carregar_entidade("bandido", x, y)
                if modelo in bandidos_atuais:
                    bandidos_atuais.remove(modelo)

            if novo is None:
                break

            novo.altura = 0
            self._resetar_estado_bandido(novo)
            novo.xp_recompensa = 34
            novo.xp_missao_id = "missao_bandido_bernardo"
            novo.xp_recompensada = False
            recomposicao.append(novo)

        self.bandidos = recomposicao[:2]
        self.bandidos_derrotados = 0
        self.ultimo_bandido_morto = None
        self._machado_spawnado = False
        self._bandidos_mortos_registrados = set()

        if (
            self.machado is not None
            and not self.machado.coletado
            and self.machado in self.cenario.itens_interativos
        ):
            self.cenario.itens_interativos.remove(self.machado)
        self.machado = None

    def _resetar_estado_bandido(self, bandido):
        bandido.vida = bandido.VIDA_MAXIMA
        bandido.destino_x = bandido.x
        bandido.destino_y = bandido.y
        bandido.defesa_ativa = False
        bandido.perfect_block = False
        bandido._tempo_defesa_esqueleto = 0.0
        bandido._cooldown_defesa_esqueleto = 0.0

        estado = getattr(bandido.animacoes, "estado", None)
        if estado is not None:
            with suppress(Exception):
                bandido.animacoes.definir(
                    "ocioso_flip" if bandido.animacoes.flip else "ocioso"
                )

        ctrl = self.cenario.controladores.get(bandido)
        if ctrl is not None:
            for acao in ctrl.get("acoes", {}).values():
                usecase = acao.get("usecase")
                cancelar = getattr(usecase, "cancelar", None)
                if cancelar is not None:
                    cancelar()
                elif usecase is not None:
                    usecase.entidade_alvo = None

    def definir_bandidos(self, bandidos):
        self.bandidos = list(bandidos)
        self.bandidos_derrotados = 0
        self.ultimo_bandido_morto = None
        self._bandidos_mortos_registrados = set()

    def _atualizar_combate_bandidos(self):
        mortos_agora = [e for e in self.bandidos if getattr(e, "vida", 0) <= 0]
        novos_mortos = [
            e for e in mortos_agora if id(e) not in self._bandidos_mortos_registrados
        ]
        for bandido in novos_mortos:
            self._bandidos_mortos_registrados.add(id(bandido))
            self.ultimo_bandido_morto = bandido

        self.bandidos_derrotados = len(self._bandidos_mortos_registrados)

        if (
            self.bandidos_derrotados >= len(self.bandidos) >= 2
            and not self._machado_spawnado
        ):
            bandido = self.ultimo_bandido_morto
            if bandido is not None:
                self.machado = ItemInterativo(
                    "machado",
                    bandido.x,
                    bandido.y,
                    "Machado de Bernardo",
                    tipo_sprite="machado",
                )
                self.cenario.itens_interativos.append(self.machado)
                self._machado_spawnado = True
                self.estado = "machado_com_sapudo"

    @staticmethod
    def _distancia(a, b):
        return hypot(a.x - b.x, a.y - b.y)

    def _entregar_machado(self):
        self.inventario["machado"] = False
        self.estado = "bernardo_trabalhando"
        self.casa_fase = "coletando"
        self.casa_madeira_entregue = 0
        self.casa_madeira_para_transportar = 0
        self._preparar_local_casa()
        self._garantir_bernardo_cortando()
        self._dialogo(
            [
                (
                    "aldeao",
                    "Bernardo",
                    "Agora preciso de um martelo, pois machados não são muito bons em construções!",
                ),
                (
                    "aldeao",
                    "Bernardo",
                    "Talvez encontre algum na mesma região onde conseguiu o machado!",
                ),
                (
                    "sapudo",
                    "Sapudo",
                    "Ainda mais trabalho ? Acabei de enfrentar dois bandidos trapalhões!",
                ),
                (
                    "aldeao",
                    "Bernardo",
                    "Então tente enfrentar mais algum! A noite se aproxima!",
                ),
                ("sapudo", "Sapudo", "Lá vou eu de novo!"),
            ],
            self._iniciar_missao_planalto,
        )

    def _iniciar_missao_planalto(self):
        self.estado = "aguardando_roubao"
        self.cobras_missao = []
        self.cobras_derrotadas = 0
        self.caverna_missao = self._obter_caverna_planalto()
        self._roubao_dialogo_iniciado = False
        self._roubao_retorno_iniciado = False

        casa = self._casa_palha_vermelha()
        if casa is None:
            return

        if self.roubao is not None:
            self.cenario.remover_personagem(self.roubao)

        posicao = self._posicao_frente_casa(casa)
        self.roubao = self.cenario.carregar_entidade("bandido", *posicao)
        if self.roubao is not None:
            self.roubao.definir_base_movimento(self.roubao.x, self.roubao.y)
            self.roubao.destino_x = self.roubao.x
            self.roubao.destino_y = self.roubao.y
            self.roubao.altura = 0
            self.roubao.xp_recompensa = 0
            self.roubao.xp_missao_id = None
            self.roubao.xp_recompensada = True
            self._definir_roubao_ocioso()

    def _posicao_frente_casa(self, casa):
        candidatos = (
            (casa.x, casa.y + 112),
            (casa.x - 112, casa.y + 24),
            (casa.x + 112, casa.y + 24),
            (casa.x, casa.y - 112),
        )
        for x, y in candidatos:
            try:
                if self.cenario.navegacao.pode_andar(x, y, 0):
                    return x, y
            except Exception:
                continue
        return candidatos[0]

    def _definir_roubao_ocioso(self):
        if self.roubao is None:
            return
        self.roubao.destino_x = self.roubao.x
        self.roubao.destino_y = self.roubao.y
        self.roubao.animacoes.definir(
            "ocioso",
            flip=self.roubao.flip,
        )

    def _orientar_roubao_para_sapudo(self):
        if self.roubao is None:
            return
        sapudo = self._sapudo()
        if sapudo is None:
            return

        self.roubao.animacoes.definir_por_direcao("ocioso", sapudo.x - self.roubao.x)

        sapudo.animacoes.definir_por_direcao("ocioso", self.roubao.x - sapudo.x)

    def _atualizar_encontro_roubao(self):
        if self.roubao is None or self._roubao_dialogo_iniciado:
            return

        sapudo = self._sapudo()
        if sapudo is None:
            return

        if self._perto(sapudo, self.roubao.x, self.roubao.y, raio=125):
            self._orientar_roubao_para_sapudo()
            self._roubao_dialogo_iniciado = True
            self.estado = "dialogo_roubao"
            self._dialogo(
                [
                    ("sapudo", "Sapudo", "Boa tarde senhor de vestimenta esquisita!"),
                    (
                        "sapudo",
                        "Sapudo",
                        "Por acaso teria algum machado para negociar?",
                    ),
                    (
                        "bandido",
                        "Roubão",
                        "Por acaso irá negociar da mesma maneira que fez com meus amigos aqui?",
                    ),
                    (
                        "sapudo",
                        "Sapudo",
                        "Eles queriam descobrir se minha espada funciona! Não foi bem culpa minha!",
                    ),
                    (
                        "bandido",
                        "Roubão",
                        "Pois saiba que se tentar me atacar nunca conseguirá o que procura!",
                    ),
                    ("sapudo", "Sapudo", "E como conseguirei então?"),
                    (
                        "bandido",
                        "Roubão",
                        "Guardei meu tesouro em uma caverna acima a algum tempo atrás, mas agora a região está tomada por cobras, derrote-as e poderei te dar um martelo.",
                    ),
                    (
                        "sapudo",
                        "Sapudo",
                        "Que seja, que risco podem oferecer algumas cobras?",
                    ),
                ],
                self._revelar_cobras_planalto,
            )

    def _revelar_cobras_planalto(self):
        if self.roubao is not None:
            self.cenario.remover_personagem(self.roubao)
            self.roubao = None

        self.estado = "missao_planalto_cobras"
        self._criar_cobras_planalto()

    def _criar_cobras_planalto(self):
        cobras_existentes = [
            cobra
            for cobra in getattr(self, "cobras_missao", [])
            if cobra is not None
            and cobra in getattr(self.cenario, "personagens_hostis", ())
            and getattr(cobra, "nome", None) == "cobra"
        ]
        if cobras_existentes:
            self.cobras_missao = cobras_existentes
            self.cobras_derrotadas = max(0, 5 - len(cobras_existentes))
            return

        self.cobras_missao = []
        self.cobras_derrotadas = 0

        caverna = self.caverna_missao or self._obter_caverna_planalto()
        if caverna is None:
            return
        self.caverna_missao = caverna

        sapudo = self._sapudo()
        nivel_sapudo = max(1, int(getattr(sapudo, "nivel", 1))) if sapudo else 1
        dano_maximo_sapudo = max(1, int(getattr(sapudo, "ataque", 1))) if sapudo else 1

        vida_caverna = max(6, round(dano_maximo_sapudo * 0.75 + nivel_sapudo))
        self.caverna_missao.VIDA_MAXIMA = vida_caverna
        self.caverna_missao.vida = vida_caverna
        self.caverna_missao.missao_id = "missao_cobras_planalto"
        self.caverna_missao.condicao_ataque = "apos_cobras"

        altura = 1
        tilemap = getattr(self.cenario, "tilemap_renderer", None)
        candidatos = []

        if tilemap is not None:
            cx_col, cx_lin = tilemap.pixel_para_tile(caverna.x, caverna.y)
            for dc in range(-3, 4):
                for dl in range(-3, 4):
                    col = cx_col + dc
                    lin = cx_lin + dl
                    x0, y0 = tilemap.tile_para_pixel(col, lin)
                    x = x0 + TILE_SIZE / 2
                    y = y0 + TILE_SIZE / 2
                    try:
                        if not tilemap.pode_andar_pixel(x, y, altura, margem_borda=0):
                            continue
                        regiao = tilemap.obter_regiao_no_ponto(x, y)
                        if (
                            regiao is not None
                            and getattr(regiao, "id", None) != "planalto_norte"
                        ):
                            continue
                    except Exception:
                        continue
                    candidatos.append((hypot(x - caverna.x, y - caverna.y), x, y))

        if not candidatos:
            candidatos = [
                (hypot(dx, dy), caverna.x + dx, caverna.y + dy)
                for dx, dy in ((-96, -32), (0, -32), (96, -32), (-64, 32), (64, 32))
            ]

        candidatos.sort()
        usados = []
        for _, x, y in candidatos:
            if any(hypot(x - ux, y - uy) < 48 for ux, uy in usados):
                continue

            cobra = self.cenario.carregar_entidade("cobra", x, y)
            if cobra is None:
                continue

            vida_cobra = max(40, int(dano_maximo_sapudo * (4.5 + 0.25 * nivel_sapudo)))
            ataque_cobra = max(5, int(round(dano_maximo_sapudo * 0.50)) + nivel_sapudo)
            defesa_cobra = max(2, int(round(dano_maximo_sapudo * 0.20)))

            cobra.VIDA_MAXIMA = vida_cobra
            cobra.vida = vida_cobra
            cobra.ataque = ataque_cobra
            cobra.defesa = defesa_cobra
            cobra.altura = altura
            cobra.definir_base_movimento(cobra.x, cobra.y)
            cobra.xp_recompensa = 40
            cobra.xp_missao_id = "missao_cobras_planalto"
            cobra.xp_recompensada = False
            self.cobras_missao.append(cobra)
            usados.append((x, y))

            if len(self.cobras_missao) >= 5:
                break

    def _atualizar_missao_cobras(self):
        vivos = [c for c in self.cobras_missao if getattr(c, "vida", 0) > 0]
        self.cobras_derrotadas = len(self.cobras_missao) - len(vivos)

        if self.cobras_missao and self.cobras_derrotadas >= 5:
            if self.evolucao_pendente:
                return
            self._iniciar_retorno_roubao()

    def _iniciar_retorno_roubao(self):
        if self._roubao_retorno_iniciado:
            return
        sapudo = self._sapudo()
        if sapudo is None:
            return

        x_esquerda = self.cenario.tilemap_renderer.offset_x + TILE_SIZE * 2
        y = sapudo.y
        self.roubao = self.cenario.carregar_entidade("bandido", x_esquerda, y)
        if self.roubao is None:
            return

        self.roubao.altura = 0
        self.roubao.xp_recompensa = 0
        self.roubao.xp_missao_id = None
        self.roubao.xp_recompensada = True
        self.roubao.definir_base_movimento(self.roubao.x, self.roubao.y)
        self.roubao.destino_x = self.roubao.x
        self.roubao.destino_y = self.roubao.y
        self._roubao_retorno_iniciado = True
        self.estado = "roubao_retornando"

    def _atualizar_retorno_roubao(self, dt):
        sapudo = self._sapudo()
        if sapudo is None or self.roubao is None:
            return

        dx = sapudo.x - self.roubao.x
        dy = sapudo.y - self.roubao.y
        distancia = hypot(dx, dy)

        if abs(dx) > 0.0001:
            self.roubao.animacoes.definir_por_direcao("correndo", dx)

        if distancia <= 82:
            self._orientar_roubao_para_sapudo()
            self.roubao.destino_x = self.roubao.x
            self.roubao.destino_y = self.roubao.y
            self.estado = "dialogo_roubao"
            self._dialogo(
                [
                    (
                        "bandido",
                        "Roubão",
                        "Finalmente irei recuperar meu brilhante tesouro! Pegue este martelo!",
                    ),
                    (
                        "sapudo",
                        "Sapudo",
                        "Um martelo de madeira? Lutei com cobras por isto ?",
                    ),
                    (
                        "bandido",
                        "Roubão",
                        "Se não gostou, pode procurar outro seu reclamão! Tchal Tchal.",
                    ),
                ],
                self._disponibilizar_martelo,
            )
            return

        alvo = (sapudo.x - 72, sapudo.y)
        self._movimento_roubao.executar(
            personagem=self.roubao,
            navegacao=self.cenario.navegacao,
            velocidade=125,
            estado_correndo="correndo",
            estado_correndo_flip="correndo_flip",
            estado_parado="ocioso",
            estado_parado_flip="ocioso_flip",
            dt=dt,
            destino_externo=alvo,
        )

    def _disponibilizar_martelo(self):
        if self.roubao is None:
            return

        self.martelo = ItemInterativo(
            "martelo",
            self.roubao.x,
            self.roubao.y,
            "Martelo de Bernardo",
            tipo_sprite="martelo",
        )
        self.cenario.itens_interativos.append(self.martelo)

        ctrl = self.cenario.controladores.get(self.roubao)
        if ctrl is not None:
            ataque = ctrl.get("acoes", {}).get("atacar")
            if ataque is not None:
                ataque["usecase"].entidade_alvo = None
        self.roubao.destino_x = self.roubao.x
        self.roubao.destino_y = self.roubao.y
        self._roubao_saida_ativa = True
        self.estado = "roubao_saida"
        self._roubao_saida_iniciada = True

    def _atualizar_saida_roubao(self, dt):
        if self.roubao is None:
            self._roubao_saida_ativa = False
            self.estado = "martelo_com_sapudo"
            return

        caverna = self._obter_caverna_planalto()
        if caverna is None:
            self.cenario.remover_personagem(self.roubao)
            self.roubao = None
            self._roubao_saida_ativa = False
            self.estado = "martelo_com_sapudo"
            return

        distancia = hypot(self.roubao.x - caverna.x, self.roubao.y - caverna.y)

        if distancia <= 48:
            self.cenario.remover_personagem(self.roubao)
            self.roubao = None
            self._roubao_saida_ativa = False
            self.estado = "martelo_com_sapudo"
            self.caverna_missao = None
            return

        velocidade = 125.0
        passo = velocidade * max(0.0, dt)

        dx = caverna.x - self.roubao.x
        dy = caverna.y - self.roubao.y
        distancia = hypot(dx, dy)

        if distancia <= max(48.0, passo):
            self.roubao.x = caverna.x
            self.roubao.y = caverna.y
            self.cenario.remover_personagem(self.roubao)
            self.roubao = None
            self._roubao_saida_ativa = False
            self.estado = "martelo_com_sapudo"
            self.caverna_missao = None
            return

        self.roubao.x += (dx / distancia) * passo
        self.roubao.y += (dy / distancia) * passo
        self.roubao.destino_x = caverna.x
        self.roubao.destino_y = caverna.y

        self.roubao.flip = self.roubao.animacoes.flip_para_direcao(dx)
        self.roubao.animacoes.definir(
            "correndo",
            flip=self.roubao.flip,
        )

    def _obter_caverna_planalto(self):
        candidatos = [
            c
            for c in self.cenario.construcoes_hostis
            if getattr(c, "nome", None) == "caverna"
        ]
        if not candidatos:
            return None
        if self.cenario.world_context is None:
            return candidatos[0]
        for candidata in candidatos:
            with suppress(Exception):
                loc = self.cenario.world_context.localizar(candidata.x, candidata.y)
                if (
                    getattr(loc, "regiao", None) is not None
                    and loc.regiao.id == "planalto_norte"
                ):
                    return candidata

        return candidatos[0]

    def _garantir_cobras_ativas(self, cobras):
        for cobra in cobras:
            ctrl = self.cenario.controladores.get(cobra)
            if ctrl is None:
                continue

            atacar = ctrl.get("acoes", {}).get("atacar")
            if (
                atacar is not None
                and getattr(atacar.get("usecase"), "entidade_alvo", None) is not None
            ):
                continue

            maquina = getattr(cobra.animacoes, "maquina", None)
            if maquina is not None and maquina.atacando():
                continue

            estado = getattr(cobra.animacoes, "estado", None)
            estado_cobranca = getattr(estado, "name", "")
            esta_correndo = estado_cobranca in {"CORRENDO", "CORRENDO_FLIP"}
            if (
                esta_correndo
                and hypot(cobra.x - cobra.destino_x, cobra.y - cobra.destino_y) > 10
            ):
                continue

            try:
                destino = self.cenario.navegacao.ponto_aleatorio_no_raio(
                    cobra.base_x,
                    cobra.base_y,
                    1,
                    48,
                    min(cobra.raio_movimento_livre, TILE_SIZE * 3),
                )
            except Exception:
                destino = None

            if destino is None:
                candidatos = [
                    (outra.base_x, outra.base_y)
                    for outra in cobras
                    if outra is not cobra
                ]
                candidatos.append((cobra.base_x, cobra.base_y))
                for candidato in candidatos:
                    try:
                        if self.cenario.navegacao.pode_andar(
                            candidato[0], candidato[1], 1
                        ):
                            destino = candidato
                            break
                    except Exception:
                        continue

            if destino is None:
                continue

            cobra.destino_x, cobra.destino_y = destino
            with suppress(Exception):
                cobra.animacoes.definir(
                    "correndo_flip" if destino[0] < cobra.x else "correndo"
                )

    def _atualizar_missao_caverna(self):
        return

    def notificar_construcao_destruida(self, construcao):
        return

    def _conversar_martelo(self):
        self._dialogo(
            [
                ("aldeao", "Bernardo", "De madeira? Um martelo de madeira?"),
                ("aldeao", "Bernardo", "Bem, é melhor que nada!"),
                (
                    "sapudo",
                    "Sapudo",
                    "Irei aguardar, se precisar de ajuda para carregar madeira ou martelar...",
                ),
                (
                    "sapudo",
                    "Sapudo",
                    "Então não poderei ajudar, pois a armadura me impede de carregar ainda mais peso!",
                ),
                ("aldeao", "Bernardo", "Sei, sei..."),
            ],
            self._finalizar_casa_com_martelo,
        )

    def _finalizar_casa_com_martelo(self):
        self.inventario["martelo"] = False
        self.martelo_recebido_por_bernardo = True
        if self._iniciar_construcao_se_pronta():
            return

        if self.casa_fase not in (None, "pronta", "construindo"):
            self.estado = (
                "casa_construindo"
                if self.casa_fase == "aguardando_martelo"
                else "bernardo_trabalhando"
            )

    def _iniciar_construcao_se_pronta(self):
        if (
            not self.martelo_recebido_por_bernardo
            or self.casa_construindo is None
            or self.casa_madeira_entregue < self.CASA_MADEIRA_NECESSARIA
        ):
            return False

        self.casa_fase = "construindo"
        self.estado = "casa_construindo"
        self.construir_casa.concluida_callback = self._casa_construida
        self.construir_casa.iniciar(
            bernardo=self.bernardo,
            casa=self.casa_construindo,
            ponto_entrega=self.casa_ponto_entrega,
            quantidade_madeira=self.casa_madeira_entregue,
        )
        return True

    def _casa_construida(self, casa):
        self._remover_madeiras_da_construcao()
        self.casa_construindo = None
        self.casa_fase = "pronta"
        self.estado = "casa_pronta"
        self.casa_madeira_entregue = 0
        self.casa_madeira_para_transportar = 0
        self._dialogo_martelo_pronto = False
        self.roubao = None
        self._roubao_retorno_iniciado = False
        self._roubao_dialogo_iniciado = False
        self._movimento_roubao = MoverPersonagemUseCase()
        self.cenario.notificar_obstaculos_alterados()

    def _garantir_casa_construindo_visivel(self):
        """Mantém a construção temporária registrada e visível no renderer."""
        casa = self.casa_construindo
        if casa is None:
            return
        with suppress(Exception):
            casa.visivel = True
            casa.proprietario_bernardo = True
            construcoes = getattr(self.cenario, "construcoes", None)
            if construcoes is not None and casa not in construcoes:
                self.cenario.adicionar_personagem(casa, "construcoes")
            registro = getattr(self.cenario, "_registro_entidades", {}).get(casa)
            render_regs = getattr(self.cenario, "_render_registros", [])
            if registro is not None and not any(
                item.get("entidade") is casa for item in render_regs
            ):
                cfg = self.cenario._obter_renderer(
                    casa.nome,
                    __import__(
                        "data.sprites_config", fromlist=["obter_config"]
                    ).obter_config(casa.nome),
                )
                renderer_cfg = (
                    __import__("data.sprites_config", fromlist=["obter_config"])
                    .obter_config(casa.nome)
                    .get("renderer", {})
                )
                render_regs.append(
                    {
                        "entidade": casa,
                        "renderer": registro.get("renderer", cfg),
                        "escala": renderer_cfg.get("escala", 1.0) or 1.0,
                        "grupo": registro.get("grupo", "construcoes"),
                    }
                )
            # A construção temporária tem uma animação estática própria.
            casa.animacoes.definir(
                "ocioso", flip=getattr(casa.animacoes, "flip", False)
            )

    def _remover_madeiras_da_construcao(self):
        """Remove madeira física já entregue ao ponto de construção."""
        if self.casa_ponto_entrega is None:
            return
        px, py = self.casa_ponto_entrega
        for recurso in list(getattr(self.cenario, "recursos", ())):
            if getattr(recurso, "nome", None) != "madeira":
                continue
            if getattr(recurso, "madeira_missao_bernardo", False) or (
                hypot(recurso.x - px, recurso.y - py) <= 20
            ):
                with suppress(Exception):
                    self.cenario.remover_personagem(recurso, ignorar=self.bernardo)

    def _atualizar_construcao_bernardo(self, dt):
        if self.casa_fase is None or self.casa_fase == "pronta":
            return

        if self.casa_fase == "construindo":
            self._garantir_casa_construindo_visivel()
            if not self.construir_casa.ativo:
                if (
                    self.martelo_recebido_por_bernardo
                    and self.casa_construindo is not None
                    and self.bernardo is not None
                ):
                    restante = int(getattr(self.construir_casa, "madeira_restante", 0))
                    if restante <= 0:
                        restante = max(
                            1,
                            self.CASA_MADEIRA_NECESSARIA
                            - int(self.casa_madeira_entregue),
                        )
                    self.construir_casa.retomar(
                        bernardo=self.bernardo,
                        casa=self.casa_construindo,
                        ponto_entrega=self.casa_ponto_entrega,
                        quantidade_madeira=restante,
                        tempo=getattr(self.construir_casa, "tempo", 0.0),
                        flip=getattr(self.construir_casa, "flip", False),
                    )
                else:
                    return
            self.construir_casa.executar(dt)
            return

        if self.casa_fase == "coletando":
            usecase = self._garantir_bernardo_cortando()
            if usecase is not None:
                usecase.executar(dt)

            if self.cenario.total_madeira >= self.CASA_MADEIRA_NECESSARIA:
                self._cancelar_acoes_bernardo()
                self.casa_madeira_para_transportar = (
                    self.CASA_MADEIRA_NECESSARIA - self.casa_madeira_entregue
                )
                self._sincronizar_madeiras_do_deposito()
                self.casa_fase = "indo_deposito"
            return

        if self.casa_fase == "aguardando_martelo":
            if (
                self.bernardo.animacoes.esta_em("correndo_madeira")
                or self.bernardo.animacoes.esta_em("correndo_ouro")
                or self.bernardo.animacoes.esta_em("correndo_carne")
            ):
                self.bernardo.animacoes.definir(
                    "ocioso_flip" if getattr(self.bernardo, "flip", False) else "ocioso"
                )
            self.bernardo.destino_x = self.bernardo.x
            self.bernardo.destino_y = self.bernardo.y
            return

        if self.casa_fase == "indo_deposito":
            madeira = self._encontrar_madeira_no_deposito()
            if madeira is None:
                self._aguardar_bernardo(dt)
                return

            if self._bernardo_chegou(madeira.x, madeira.y):
                self.cenario.remover_personagem(madeira, ignorar=self.bernardo)
                self.cenario.remover_estoque("madeira", 1)
                self.casa_madeira_para_transportar = max(
                    0, self.casa_madeira_para_transportar - 1
                )
                self.casa_fase = "indo_casa"
                destino = self.casa_ponto_entrega or self.casa_posicao

                self._orientar_bernardo_para_entrega(*destino)
                self._mover_bernardo_para(*destino, carregando=True, dt=dt)
                return

            self._mover_bernardo_para(madeira.x, madeira.y, carregando=False, dt=dt)
            return

        if self.casa_fase == "indo_casa":
            destino = self.casa_ponto_entrega or self.casa_posicao
            if destino is None:
                return

            if self._bernardo_chegou(*destino):
                if self.casa_construindo is None:
                    self.casa_construindo = self.cenario.carregar_entidade(
                        "casa_construindo", *self.casa_posicao
                    )
                    self.casa_construindo.proprietario_bernardo = True
                    self._garantir_casa_construindo_visivel()
                    self.cenario.notificar_obstaculos_alterados()

                self.cenario.carregar_entidade("madeira", *destino)
                self.casa_madeira_entregue += 1

                if self.casa_madeira_entregue >= self.CASA_MADEIRA_NECESSARIA:
                    self.bernardo.animacoes.definir(
                        "ocioso",
                        flip=self.bernardo.flip,
                    )
                    self.bernardo.destino_x = self.bernardo.x
                    self.bernardo.destino_y = self.bernardo.y
                    self.casa_fase = "aguardando_martelo"
                    self._iniciar_construcao_se_pronta()
                else:
                    self.casa_fase = "indo_deposito"
                return

            self._mover_bernardo_para(*destino, carregando=True, dt=dt)
            return

    def _preparar_local_casa(self):
        if self.casa_posicao is not None:
            if self.casa_ponto_entrega is None:
                self.casa_ponto_entrega = self._encontrar_ponto_entrega_casa(
                    self.casa_posicao
                )
            return self.casa_ponto_entrega is not None

        sapudo = self._sapudo()
        candidatos = (
            (-260, 70),
            (-210, 130),
            (-180, -140),
            (-300, 40),
            (170, 70),
            (-170, 70),
            (210, 130),
            (180, -140),
            (260, 40),
            (-260, 40),
        )
        for dx, dy in candidatos:
            x = self.bernardo.x + dx
            y = self.bernardo.y + dy
            if sapudo is not None and hypot(x - sapudo.x, y - sapudo.y) < 190:
                continue
            if self.cenario.navegacao.pode_andar(
                x, y, getattr(self.bernardo, "altura", 0)
            ):
                self.casa_posicao = (x, y)
                self.casa_ponto_entrega = self._encontrar_ponto_entrega_casa(
                    self.casa_posicao
                )
                if self.casa_ponto_entrega is not None:
                    return True
                self.casa_posicao = None
        return False

    def _encontrar_ponto_entrega_casa(self, casa_posicao):
        x, y = casa_posicao
        candidatos = (
            (x + TILE_SIZE, y),
            (x - TILE_SIZE, y),
            (x, y + TILE_SIZE),
            (x, y - TILE_SIZE),
            (x + TILE_SIZE, y + TILE_SIZE),
            (x - TILE_SIZE, y + TILE_SIZE),
            (x + TILE_SIZE, y - TILE_SIZE),
            (x - TILE_SIZE, y - TILE_SIZE),
        )
        altura = getattr(self.bernardo, "altura", 0)
        for candidato in candidatos:
            try:
                if self.cenario.navegacao.pode_andar(
                    candidato[0], candidato[1], altura
                ):
                    return candidato
            except Exception:
                continue
        return None

    def _sincronizar_madeiras_do_deposito(self):
        estoque = max(0, int(getattr(self.cenario, "estoque", {}).get("madeira", 0)))
        if estoque <= 0:
            return

        referencia_x = 510
        referencia_y = 425
        limite = TILE_SIZE * 2.0

        madeiras_missao = []
        madeiras_sem_marcador = []
        for recurso in getattr(self.cenario, "recursos", ()):
            if getattr(recurso, "nome", None) != "madeira":
                continue
            distancia = hypot(recurso.x - referencia_x, recurso.y - referencia_y)
            if distancia <= limite:
                if getattr(recurso, "madeira_missao_bernardo", False):
                    madeiras_missao.append(recurso)
                else:
                    madeiras_sem_marcador.append(recurso)

        existentes = len(madeiras_missao) + len(madeiras_sem_marcador)
        faltantes = max(0, estoque - existentes)

        for indice in range(faltantes):
            coluna = indice % 5
            linha = indice // 5
            x = referencia_x + (coluna - 2) * 18
            y = referencia_y + linha * 16
            madeira = self.cenario.carregar_entidade("madeira", x, y)
            if madeira is None:
                continue
            with suppress(Exception):
                madeira.madeira_missao_bernardo = True

    def _encontrar_madeira_no_deposito(self):
        referencia_x = 510
        referencia_y = 425
        melhores = []
        for recurso in getattr(self.cenario, "recursos", ()):
            if getattr(recurso, "nome", None) != "madeira":
                continue
            distancia = hypot(recurso.x - referencia_x, recurso.y - referencia_y)
            if distancia <= TILE_SIZE * 2.0:
                melhores.append((distancia, recurso))
        if not melhores:
            return None
        melhores.sort(key=lambda item: item[0])
        return melhores[0][1]

    def _arvore_para_noite(self, bernardo):
        arvores = getattr(self.cenario, "arvores", ())
        melhor = None
        menor = None
        for arvore in arvores:
            try:
                if not getattr(arvore, "pronta_para_coleta", True):
                    continue
                if getattr(arvore, "madeira", 0) <= 0:
                    continue
                distancia = hypot(arvore.x - bernardo.x, arvore.y - bernardo.y)
                if distancia <= RecolherBernardoUseCase.RAIO_BUSCA_ARVORE and (
                    menor is None or distancia < menor
                ):
                    menor = distancia
                    melhor = arvore
            except Exception:
                continue
        return melhor

    def _aguardar_bernardo(self, dt):
        self.bernardo.destino_x = self.bernardo.x
        self.bernardo.destino_y = self.bernardo.y
        self.bernardo.animacoes.definir(
            "ocioso",
            flip=self.bernardo.flip,
        )

    def _cancelar_acoes_bernardo(self):
        ctrl = self.cenario.controladores.get(self.bernardo)
        if ctrl is None:
            return
        for acao in ctrl.get("acoes", {}).values():
            usecase = acao.get("usecase")
            cancelar = getattr(usecase, "cancelar", None)
            if callable(cancelar):
                cancelar()
            elif usecase is not None:
                usecase.entidade_alvo = None

    def _bernardo_chegou(self, x, y):
        return hypot(self.bernardo.x - x, self.bernardo.y - y) <= 20

    def _orientar_bernardo_para_entrega(self, x, y):
        if self.bernardo is None:
            return

        dx = x - self.bernardo.x
        if abs(dx) <= 0.0001:
            return

        self.bernardo.animacoes.definir_por_direcao("correndo_madeira", dx)
        self.bernardo.flip = self.bernardo.animacoes.flip

    def _mover_bernardo_para(self, x, y, carregando, dt):
        self.bernardo.destino_x = x
        self.bernardo.destino_y = y
        animacao = "correndo_madeira" if carregando else "correndo"
        self.cenario.mover_personagem.executar(
            personagem=self.bernardo,
            navegacao=self.cenario.navegacao,
            velocidade=110,
            dt=dt,
            animacao_correndo=animacao,
            animacao_parado="ocioso",
        )

    def _finalizar_casa(self):
        if self.casa_construindo is None:
            return
        x, y = self.casa_construindo.x, self.casa_construindo.y
        self.cenario.remover_personagem(self.casa_construindo)
        casa = self.cenario.carregar_entidade("casa_palha_azul", x, y)
        casa.proprietario_bernardo = True
        self.casa_construindo = None
        self.casa_fase = "pronta"
        self.estado = "casa_pronta"
        self.cenario.notificar_obstaculos_alterados()

    def _garantir_bernardo_cortando(self):
        if (
            self.bernardo is None
            or self.cenario.total_madeira >= self.CASA_MADEIRA_NECESSARIA
        ):
            return None
        if self.casa_fase not in (None, "coletando"):
            return None

        ctrl = self.cenario.controladores.get(self.bernardo)
        if ctrl is None:
            return None

        acao = ctrl.get("acoes", {}).get("arvore")
        if acao is None:
            return None

        usecase = acao.get("usecase")
        if usecase is None:
            return None

        if getattr(usecase, "entidade_alvo", None) is not None:
            return usecase

        buscar = getattr(usecase, "_buscar_arvore_proxima", None)
        iniciar = getattr(usecase, "iniciar", None)
        if not callable(buscar) or not callable(iniciar):
            return None

        arvore = buscar(
            origem_x=self.bernardo.x,
            origem_y=self.bernardo.y,
            excluir=None,
        )

        if arvore is None:
            disponivel = getattr(usecase, "_arvore_disponivel", None)
            for candidata in getattr(self.cenario, "arvores", ()):
                if callable(disponivel) and disponivel(candidata):
                    arvore = candidata
                    break

        if arvore is None:
            return None

        if iniciar(arvore, self.bernardo):
            return usecase

        return None

    def _construir_casa(self):
        if self._casa_bernardo() is not None:
            self.estado = "casa_pronta"
            return

        sapudo = self._sapudo()
        candidatos = (
            (-260, 70),
            (-210, 130),
            (-180, -140),
            (-300, 40),
            (170, 70),
            (-170, 70),
            (210, 130),
            (180, -140),
            (260, 40),
            (-260, 40),
        )

        for dx, dy in candidatos:
            x = self.bernardo.x + dx
            y = self.bernardo.y + dy
            if sapudo is not None and hypot(x - sapudo.x, y - sapudo.y) < 190:
                continue

            casa = self.cenario.carregar_entidade("casa", x, y)
            if self.cenario.posicao_construcao_valida(casa):
                self.cenario.estoque["madeira"] -= self.CASA_MADEIRA_NECESSARIA
                casa.proprietario_bernardo = True
                self.cenario.notificar_obstaculos_alterados()
                self.estado = "casa_pronta"
                return
            self.cenario.remover_personagem(casa)

    def _casa_bernardo(self):
        for construcao in self.cenario.construcoes:
            if getattr(construcao, "proprietario_bernardo", False):
                return construcao

        if self.casa_fase in ("pronta",) and self.casa_posicao is not None:
            with suppress(Exception):
                casa = self.cenario.carregar_entidade(
                    "casa_palha_azul",
                    float(self.casa_posicao[0]),
                    float(self.casa_posicao[1]),
                )
                if casa is not None:
                    casa.proprietario_bernardo = True
                    casa.visivel = True
                    if casa not in self.cenario.construcoes:
                        self.cenario.adicionar_personagem(casa, "construcoes")
                    self.cenario.notificar_obstaculos_alterados()
                    return casa

        return None

    def _dialogo(self, linhas, callback):
        if self.renderer is None:
            return
        self.aberta = True
        self.renderer.iniciar(linhas, callback)

    def _sapudo(self):
        for personagem in self.cenario.personagens:
            if personagem.nome == "sapudo":
                return personagem
        return None

    @staticmethod
    def _perto(entidade, x, y, raio=None):
        return hypot(entidade.x - x, entidade.y - y) <= (raio or 88)
