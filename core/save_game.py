import json
from contextlib import suppress

from utils.paths import BASE_DIR

SAVE_PATH = BASE_DIR / "savegame.json"


class SaveGameManager:
    VERSION = 3

    VERSION = 4
    _CAMPOS_ENTIDADE = (
        "x",
        "y",
        "altura",
        "base_pe_y",
        "vida",
        "VIDA_MAXIMA",
        "ataque",
        "defesa",
        "visivel",
        "selecionado",
        "destino_x",
        "destino_y",
        "experiencia",
        "experiencia_total",
        "nivel",
        "pontos_evolucao",
        "defesa_ativa",
        "perfect_block",
        "madeira",
        "minerio",
        "coletado",
        "crescendo",
        "tempo_crescimento",
        "escala_x",
        "escala_y",
        "world_spawn_id",
        "world_resource_id",
        "madeira_missao_bernardo",
        "base_x",
        "base_y",
        "base_raio",
        "xp_recompensa",
        "xp_missao_id",
        "xp_recompensada",
        "missao_id",
        "condicao_ataque",
        "proprietario_bernardo",
    )

    def __init__(self, cenario):
        self.cenario = cenario
        self.ultimo_status = ""

    # ------------------------------------------------------------------
    # Identidade persistente
    # ------------------------------------------------------------------
    @staticmethod
    def _eh_entidade_cenario(cenario, valor):
        if valor is None:
            return False
        colecoes = (
            getattr(cenario, "personagens", ()),
            getattr(cenario, "personagens_hostis", ()),
            getattr(cenario, "ovelhas", ()),
            getattr(cenario, "construcoes", ()),
            getattr(cenario, "construcoes_hostis", ()),
            getattr(cenario, "arvores", ()),
            getattr(cenario, "minas_ouro", ()),
            getattr(cenario, "recursos", ()),
            getattr(cenario, "efeitos", ()),
            getattr(cenario, "flora", ()),
        )
        return any(valor in colecao for colecao in colecoes)

    @staticmethod
    def _parece_entidade(valor):
        if valor is None or isinstance(valor, (str, int, float, bool, bytes)):
            return False
        if not all(hasattr(valor, atributo) for atributo in ("nome", "x", "y")):
            return False
        return any(
            hasattr(valor, atributo)
            for atributo in (
                "vida",
                "save_id",
                "persistencia_dinamica",
                "world_spawn_id",
            )
        )

    def _entidades_referenciadas(
        self, valor, encontrados=None, profundidade=0, vistos=None
    ):
        if encontrados is None:
            encontrados = {}
        if vistos is None:
            vistos = set()
        if profundidade > 8 or valor is None:
            return encontrados
        if self._parece_entidade(valor):
            encontrados[id(valor)] = valor
            return encontrados
        if isinstance(valor, (str, int, float, bool, bytes)):
            return encontrados
        oid = id(valor)
        if oid in vistos:
            return encontrados
        vistos.add(oid)

        if isinstance(valor, dict):
            for item in valor.values():
                self._entidades_referenciadas(
                    item, encontrados, profundidade + 1, vistos
                )
        elif isinstance(valor, (list, tuple, set)):
            for item in valor:
                self._entidades_referenciadas(
                    item, encontrados, profundidade + 1, vistos
                )
        elif hasattr(valor, "__dict__"):
            for nome, item in vars(valor).items():
                if nome in {
                    "cenario",
                    "renderer",
                    "tela",
                    "assets",
                    "transform",
                    "navegacao",
                    "world_context",
                }:
                    continue
                if callable(item):
                    continue
                self._entidades_referenciadas(
                    item, encontrados, profundidade + 1, vistos
                )
        return encontrados

    def _todas_entidades(self):
        c = self.cenario
        resultado = []
        vistos = set()
        colecoes = (
            getattr(c, "personagens", ()),
            getattr(c, "personagens_hostis", ()),
            getattr(c, "ovelhas", ()),
            getattr(c, "construcoes", ()),
            getattr(c, "construcoes_hostis", ()),
            getattr(c, "arvores", ()),
            getattr(c, "minas_ouro", ()),
            getattr(c, "recursos", ()),
            getattr(c, "efeitos", ()),
            getattr(c, "flora", ()),
        )
        for colecao in colecoes:
            for entidade in colecao:
                ident = id(entidade)
                if ident not in vistos:
                    vistos.add(ident)
                    resultado.append(entidade)
        if getattr(c, "sapudo", None) is not None and id(c.sapudo) not in vistos:
            resultado.append(c.sapudo)
        return resultado

    def _garantir_id_entidade(self, entidade):
        existente = getattr(entidade, "save_id", None)
        if existente:
            return str(existente)

        world_id = getattr(entidade, "world_spawn_id", None)
        if world_id:
            ident = f"world:{world_id}"
        else:
            contador = int(getattr(self.cenario, "_proximo_save_id", 1))
            ident = f"runtime:{contador}"
            self.cenario._proximo_save_id = contador + 1

        with suppress(Exception):
            entidade.save_id = ident

        return ident

    # ------------------------------------------------------------------
    # Serialização genérica
    # ------------------------------------------------------------------
    def _serializar_valor(self, valor, _profundidade=0):
        if valor.__class__.__name__ == "ItemInterativo":
            estado = {}
            for nome in (
                "nome",
                "x",
                "y",
                "descricao",
                "raio",
                "coletado",
                "tipo_sprite",
            ):
                if hasattr(valor, nome):
                    estado[nome] = getattr(valor, nome)
            return {"__item_interativo__": estado}
        if self._eh_entidade_cenario(self.cenario, valor) or self._parece_entidade(
            valor
        ):
            return {"__entity_ref__": self._garantir_id_entidade(valor)}
        if isinstance(valor, dict):
            retorno = {}
            for chave, item in valor.items():
                try:
                    retorno[str(chave)] = self._serializar_valor(
                        item, _profundidade + 1
                    )
                except Exception:
                    continue
            return retorno
        if isinstance(valor, list):
            return [self._serializar_valor(item, _profundidade + 1) for item in valor]
        if isinstance(valor, tuple):
            return {
                "__tuple__": [
                    self._serializar_valor(item, _profundidade + 1) for item in valor
                ]
            }
        if isinstance(valor, set):
            return {
                "__set__": [
                    self._serializar_valor(item, _profundidade + 1) for item in valor
                ]
            }
        if valor is None or isinstance(valor, (str, int, float, bool)):
            return valor

        if _profundidade <= 3 and hasattr(valor, "__dict__"):
            estado = {}
            for nome, item in vars(valor).items():
                if nome in {
                    "cenario",
                    "renderer",
                    "tela",
                    "assets",
                    "transform",
                    "navegacao",
                }:
                    continue
                if callable(item):
                    continue
                try:
                    convertido = self._serializar_valor(item, _profundidade + 1)
                    if convertido is not None or item is None:
                        estado[nome] = convertido
                except Exception:
                    continue
            return {
                "__object_state__": estado,
                "__object_type__": valor.__class__.__name__,
            }
        return None

    def _serializar_controlador(self, controlador):
        estado = {}
        if controlador is None:
            return estado
        for nome, valor in vars(controlador).items():
            if nome in {
                "cenario",
                "renderer",
                "recolher_bernardo",
                "evolucao",
                "_movimento_roubao",
            }:
                continue
            convertido = self._serializar_valor(valor)
            if convertido is not None:
                estado[nome] = convertido
        return estado

    def _dados_entidade(self, entidade):
        dados = {
            "save_id": self._garantir_id_entidade(entidade),
            "nome": getattr(entidade, "nome", None),
            "persistencia_dinamica": bool(
                getattr(entidade, "persistencia_dinamica", False)
            ),
        }
        for campo in self._CAMPOS_ENTIDADE:
            if hasattr(entidade, campo):
                valor = getattr(entidade, campo)
                with suppress(Exception):
                    json.dumps(valor)
                    dados[campo] = valor

        with suppress(Exception):
            dados["flip"] = bool(getattr(entidade.animacoes, "flip", False))

        return dados

    def _coletar(self):
        c = self.cenario
        cc = getattr(c, "conversa_controller", None)

        todas = []
        vistos_objetos = set()
        for entidade in self._todas_entidades():
            if id(entidade) not in vistos_objetos:
                vistos_objetos.add(id(entidade))
                todas.append(entidade)
        referenciadas = self._entidades_referenciadas(cc)
        for entidade in referenciadas.values():
            if id(entidade) not in vistos_objetos:
                vistos_objetos.add(id(entidade))
                todas.append(entidade)

        ids_usados = set()
        entidades = []
        for entidade in todas:
            ident = self._garantir_id_entidade(entidade)
            if ident in ids_usados:
                contador = int(getattr(c, "_proximo_save_id", 1))
                while f"runtime:{contador}" in ids_usados:
                    contador += 1
                c._proximo_save_id = contador + 1
                ident = f"runtime:{contador}"
                with suppress(Exception):
                    entidade.save_id = ident

            ids_usados.add(ident)
            registro = self._dados_entidade(entidade)
            registro["no_cenario"] = bool(self._eh_entidade_cenario(c, entidade))
            entidades.append(registro)

        world_state = None
        try:
            if getattr(c, "world_context", None) is not None:
                world_state = c.world_context.state.snapshot()
        except Exception:
            world_state = None

        return {
            "version": self.VERSION,
            "ciclo": {"hora": float(c.ciclo_dia_noite.hora)},
            "descanso_sapudo": self._estado_descanso_sapudo(),
            "recolher_bernardo": self._estado_recolher_bernardo(),
            "estoque": dict(c.estoque),
            "world_state": world_state,
            "camera": {
                "x": float(getattr(c.camera, "x", 0)),
                "y": float(getattr(c.camera, "y", 0)),
            },
            "entidades": entidades,
            "perseguicao_urso": self._estado_perseguicoes_urso(),
            "retorno_caverna_urso": self._estado_retorno_caverna_urso(),
            "controlador_estado": self._serializar_controlador(cc),
            # Retido para compatibilidade com saves antigos.
            "conversa": self._conversa_legacy(cc),
            "itens_interativos": self._itens_interativos_legacy(),
        }

    def _estado_descanso_sapudo(self):
        c = self.cenario
        posicao = getattr(c, "_descanso_sapudo_posicao", None)
        if posicao is not None:
            try:
                posicao = [float(posicao[0]), float(posicao[1]), int(posicao[2])]
            except Exception:
                posicao = None
        return {
            "ativo": bool(getattr(c, "_descanso_sapudo_ativo", False)),
            "posicao": posicao,
            "fator_relogio": float(getattr(c, "_descanso_sapudo_fator_relogio", 180.0)),
        }

    def _estado_recolher_bernardo(self):
        cc = getattr(self.cenario, "conversa_controller", None)
        usecase = getattr(cc, "recolher_bernardo", None) if cc is not None else None
        if usecase is None:
            return None

        def _ponto(valor):
            if valor is None:
                return None
            try:
                return [float(valor[0]), float(valor[1])]
            except Exception:
                return None

        return {
            "ativo": bool(getattr(usecase, "ativo", False)),
            "dormindo": bool(getattr(usecase, "dormindo", False)),
            "voltando_para_inicio": bool(
                getattr(usecase, "voltando_para_inicio", False)
            ),
            "destino": _ponto(getattr(usecase, "destino", None)),
            "destino_inicial": _ponto(getattr(usecase, "destino_inicial", None)),
            "tipo_destino": getattr(usecase, "tipo_destino", None),
        }

    def _estado_perseguicoes_urso(self):
        c = self.cenario
        sapudo = getattr(c, "sapudo", None)
        if sapudo is None:
            return None
        for urso in getattr(c, "personagens_hostis", ()):
            if getattr(urso, "nome", None) != "urso":
                continue
            controlador = getattr(c, "controladores", {}).get(urso)
            ataque = controlador.get("acoes", {}).get("atacar") if controlador else None
            usecase = ataque.get("usecase") if ataque else None
            if usecase is None or getattr(usecase, "entidade_alvo", None) is not sapudo:
                continue
            if (
                getattr(urso, "visivel", True) is False
                or getattr(sapudo, "visivel", True) is False
            ):
                continue
            return {
                "urso": self._garantir_id_entidade(urso),
                "alvo": self._garantir_id_entidade(sapudo),
                "tempo": float(getattr(usecase, "tempo", 0.0)),
                "tempo_apos_golpe": float(getattr(usecase, "tempo_apos_golpe", 0.0)),
                "busca_automatica_bloqueada": bool(
                    getattr(usecase, "busca_automatica_bloqueada", False)
                ),
            }
        return None

    def _estado_retorno_caverna_urso(self):
        c = self.cenario
        if not getattr(c, "_urso_retornando_caverna", False):
            return None
        urso = getattr(c, "_urso_retornando_caverna_entidade", None)
        if urso is None or getattr(urso, "nome", None) != "urso":
            return None
        destino = getattr(c, "_urso_caverna_destino", None)
        if destino is None:
            return None
        return {
            "urso": self._garantir_id_entidade(urso),
            "destino": [float(destino[0]), float(destino[1])],
            "altura": int(getattr(urso, "altura", 0)),
        }

    def _restaurar_retorno_caverna_urso(self, estado):
        """Retoma exatamente um retorno à caverna que estava em andamento."""
        c = self.cenario
        if not isinstance(estado, dict):
            return
        entidades = self._indice_entidades()
        urso = entidades.get(str(estado.get("urso")))
        destino = estado.get("destino")
        if urso is None or getattr(urso, "nome", None) != "urso":
            return
        if not isinstance(destino, (list, tuple)) or len(destino) < 2:
            return
        if getattr(urso, "vida", 0) <= 0 or not getattr(urso, "visivel", True):
            return

        controlador = getattr(c, "controladores", {}).get(urso)
        atacar = controlador.get("acoes", {}).get("atacar") if controlador else None
        usecase = atacar.get("usecase") if atacar else None
        if usecase is not None:
            finalizar = getattr(usecase, "_finalizar_ataque", None)
            if callable(finalizar):
                with suppress(Exception):
                    finalizar()

            with suppress(Exception):
                usecase.entidade_alvo = None

        try:
            c.mover_personagem.cancelar_rota(urso)
        except Exception:
            urso.destino_x = urso.x
            urso.destino_y = urso.y

        with suppress(Exception):
            urso.altura = int(estado.get("altura", getattr(urso, "altura", 0)))
            urso.base_pe_y = urso.y

        c._urso_retornando_caverna_entidade = urso
        c._urso_caverna_destino = (float(destino[0]), float(destino[1]))
        c._urso_retornando_caverna = True
        urso.visivel = True
        urso.destino_x, urso.destino_y = c._urso_caverna_destino

        dx = c._urso_caverna_destino[0] - urso.x
        with suppress(Exception):
            urso.animacoes.definir_por_direcao("correndo", dx)

    def _restaurar_perseguicao_urso(self, estado):
        """Religa a perseguição do Urso ao Sapudo após todo o Load terminar."""
        if not isinstance(estado, dict):
            return
        entidades = self._indice_entidades()
        urso = entidades.get(str(estado.get("urso")))
        alvo = entidades.get(str(estado.get("alvo")))
        if urso is None or alvo is None:
            return
        if (
            getattr(urso, "nome", None) != "urso"
            or getattr(alvo, "nome", None) != "sapudo"
        ):
            return
        if getattr(urso, "vida", 0) <= 0 or getattr(alvo, "vida", 0) <= 0:
            return
        if not getattr(urso, "visivel", True) or not getattr(alvo, "visivel", True):
            return

        with suppress(Exception):
            tilemap = getattr(self.cenario, "tilemap_renderer", None)
            if tilemap is not None and hasattr(tilemap, "pixel_para_tile"):
                coluna, linha = tilemap.pixel_para_tile(urso.x, urso.y)
                obter_altura = getattr(tilemap, "obter_altura", None)
                if callable(obter_altura):
                    altura_real = obter_altura(coluna, linha)
                    if altura_real is not None:
                        urso.altura = int(altura_real)

        with suppress(Exception):
            urso.base_pe_y = urso.y
            urso.destino_x = urso.x
            urso.destino_y = urso.y

        controlador = getattr(self.cenario, "controladores", {}).get(urso)
        ataque = controlador.get("acoes", {}).get("atacar") if controlador else None
        usecase = ataque.get("usecase") if ataque else None
        if usecase is None:
            return

        iniciar = getattr(usecase, "iniciar_ataque_noturno", None)
        if callable(iniciar) and iniciar(urso):
            usecase.tempo = float(estado.get("tempo", 0.0))
            if hasattr(usecase, "tempo_apos_golpe"):
                usecase.tempo_apos_golpe = float(estado.get("tempo_apos_golpe", 0.0))
            usecase.busca_automatica_bloqueada = bool(
                estado.get("busca_automatica_bloqueada", False)
            )

    def _conversa_legacy(self, cc):
        if cc is None:
            return {}
        return {
            "estado": getattr(cc, "estado", None),
            "inventario": dict(getattr(cc, "inventario", {})),
            "bandidos_derrotados": int(getattr(cc, "bandidos_derrotados", 0)),
            "casa_fase": getattr(cc, "casa_fase", None),
            "casa_posicao": list(getattr(cc, "casa_posicao", None))
            if getattr(cc, "casa_posicao", None) is not None
            else None,
            "casa_ponto_entrega": list(getattr(cc, "casa_ponto_entrega", None))
            if getattr(cc, "casa_ponto_entrega", None) is not None
            else None,
            "casa_madeira_entregue": int(getattr(cc, "casa_madeira_entregue", 0)),
            "casa_madeira_para_transportar": int(
                getattr(cc, "casa_madeira_para_transportar", 0)
            ),
            "cobras_derrotadas": int(getattr(cc, "cobras_derrotadas", 0)),
            "martelo_recebido_por_bernardo": bool(
                getattr(cc, "martelo_recebido_por_bernardo", False)
            ),
            "machado_spawnado": bool(getattr(cc, "_machado_spawnado", False)),
            "dialogo_roubao_iniciado": bool(
                getattr(cc, "_roubao_dialogo_iniciado", False)
            ),
            "roubao_retorno_iniciado": bool(
                getattr(cc, "_roubao_retorno_iniciado", False)
            ),
            "roubao_saida_ativa": bool(getattr(cc, "_roubao_saida_ativa", False)),
        }

    def _itens_interativos_legacy(self):
        return [
            {
                "nome": getattr(item, "nome", None),
                "x": float(getattr(item, "x", 0)),
                "y": float(getattr(item, "y", 0)),
                "descricao": getattr(item, "descricao", ""),
                "raio": float(getattr(item, "raio", 46)),
                "tipo_sprite": getattr(item, "tipo_sprite", None),
                "coletado": bool(getattr(item, "coletado", False)),
            }
            for item in getattr(self.cenario, "itens_interativos", ())
            if not getattr(item, "coletado", False)
        ]

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    @staticmethod
    def _aplicar_entidade(entidade, dados):
        for campo in SaveGameManager._CAMPOS_ENTIDADE:
            if campo in dados and hasattr(entidade, campo):
                with suppress(Exception):
                    setattr(entidade, campo, dados[campo])
        with suppress(Exception):
            if dados.get("save_id"):
                entidade.save_id = dados.get("save_id")
            entidade.persistencia_dinamica = bool(
                dados.get(
                    "persistencia_dinamica",
                    getattr(entidade, "persistencia_dinamica", False),
                )
            )
        with suppress(Exception):
            restaurar = getattr(entidade, "restaurar_estado_save", None)
            if callable(restaurar):
                restaurar(dados)
            else:
                entidade.animacoes.definir(
                    "ocioso",
                    flip=bool(
                        dados.get("flip", getattr(entidade.animacoes, "flip", False))
                    ),
                )

    @staticmethod
    def _registro_dinamico(dados, versao):
        if "persistencia_dinamica" in dados:
            return bool(dados.get("persistencia_dinamica"))
        return versao < 2 and not dados.get("world_spawn_id")

    @staticmethod
    def _id_registro(dados, indice, versao):
        if dados.get("save_id"):
            return str(dados["save_id"])
        world_id = dados.get("world_spawn_id")
        if world_id:
            return f"world:{world_id}"

        return f"legacy:{versao}:{indice}:{dados.get('nome', 'entidade')}"

    def _remover_dinamicas_fora_do_save(self, ids_salvos):
        for entidade in list(self._todas_entidades()):
            if not getattr(entidade, "persistencia_dinamica", False):
                continue
            ident = getattr(entidade, "save_id", None)
            if ident not in ids_salvos:
                with suppress(Exception):
                    self.cenario.remover_personagem(entidade)

    def _indice_entidades(self):
        indice = {
            str(entidade.save_id): entidade
            for entidade in self._todas_entidades()
            if getattr(entidade, "save_id", None)
        }
        for ident, entidade in getattr(
            self.cenario, "_entidades_save_detached", {}
        ).items():
            indice[str(ident)] = entidade
        return indice

    def _recriar_dinamicas_salvas(self, registros, versao):
        """Recria entidades runtime salvas, inclusive referências removidas do mundo."""
        indice = self._indice_entidades()
        for indice_registro, dados in enumerate(registros):
            if not self._registro_dinamico(dados, versao):
                continue
            ident = self._id_registro(dados, indice_registro, versao)
            if ident in indice:
                continue
            nome = dados.get("nome")
            if not nome:
                continue
            try:
                entidade = self.cenario.carregar_entidade(
                    nome,
                    dados.get("x", 0),
                    dados.get("y", 0),
                    dados.get("altura", 0),
                )
            except Exception:
                entidade = None
            if entidade is None:
                continue
            with suppress(Exception):
                entidade.save_id = ident
                entidade.persistencia_dinamica = True

            if dados.get("no_cenario", True) is False:
                with suppress(Exception):
                    self.cenario.remover_personagem(entidade)

                detached = getattr(self.cenario, "_entidades_save_detached", None)
                if detached is None:
                    detached = {}
                    self.cenario._entidades_save_detached = detached
                detached[ident] = entidade
            indice[ident] = entidade

    def _materializar_entidade_legada(self, dados):
        estado = dados.get("__object_state__") if isinstance(dados, dict) else None
        if not isinstance(estado, dict):
            return None
        nome = estado.get("nome")
        if nome is None or "x" not in estado or "y" not in estado:
            return None
        if not any(
            campo in estado for campo in ("vida", "persistencia_dinamica", "save_id")
        ):
            return None

        detached = getattr(self.cenario, "_entidades_save_detached", None)
        if detached is None:
            detached = {}
            self.cenario._entidades_save_detached = detached

        ident = estado.get("save_id")
        if ident is None:
            ident = f"runtime:{int(getattr(self.cenario, '_proximo_save_id', 1))}"
            self.cenario._proximo_save_id = (
                int(getattr(self.cenario, "_proximo_save_id", 1)) + 1
            )
        ident = str(ident)

        entidade = self._indice_entidades().get(ident)
        if entidade is None:
            try:
                entidade = self.cenario.carregar_entidade(
                    nome,
                    estado.get("x", 0),
                    estado.get("y", 0),
                    estado.get("altura", 0),
                )
            except Exception:
                entidade = None
        if entidade is None:
            return None

        with suppress(Exception):
            entidade.save_id = ident
            entidade.persistencia_dinamica = bool(
                estado.get("persistencia_dinamica", True)
            )

        self._aplicar_entidade(entidade, estado)

        if estado.get("vida", 1) <= 0:
            with suppress(Exception):
                self.cenario.remover_personagem(entidade)

            detached[ident] = entidade
        return entidade

    def _migrar_referencias_legadas(self, valor):
        if isinstance(valor, dict):
            if "__object_state__" in valor:
                entidade = self._materializar_entidade_legada(valor)
                if entidade is not None:
                    return {"__entity_ref__": entidade.save_id}
                estado = valor.get("__object_state__")
                return (
                    {k: self._migrar_referencias_legadas(v) for k, v in estado.items()}
                    if isinstance(estado, dict)
                    else valor
                )
            if "__entity_ref__" in valor:
                return valor
            return {k: self._migrar_referencias_legadas(v) for k, v in valor.items()}
        if isinstance(valor, list):
            return [self._migrar_referencias_legadas(v) for v in valor]
        return valor

    def _resolver_valor(self, valor, entidades):
        if isinstance(valor, dict):
            if "__item_interativo__" in valor:
                estado = valor.get("__item_interativo__") or {}
                try:
                    from domains.interacao_item import ItemInterativo

                    item = ItemInterativo(
                        estado.get("nome", "item"),
                        estado.get("x", 0),
                        estado.get("y", 0),
                        estado.get("descricao", ""),
                        raio=estado.get("raio", 46),
                        tipo_sprite=estado.get("tipo_sprite"),
                    )
                    item.coletado = bool(estado.get("coletado", False))
                    return item
                except Exception:
                    return None
            if "__entity_ref__" in valor:
                return entidades.get(str(valor["__entity_ref__"]))
            if "__tuple__" in valor:
                return tuple(
                    self._resolver_valor(x, entidades) for x in valor["__tuple__"]
                )
            if "__set__" in valor:
                return set(self._resolver_valor(x, entidades) for x in valor["__set__"])
            if "__object_state__" in valor:
                estado = self._resolver_valor(valor["__object_state__"], entidades)
                tipo = valor.get("__object_type__")
                if tipo == "ItemInterativo" and isinstance(estado, dict):
                    with suppress(Exception):
                        from domains.interacao_item import ItemInterativo

                        item = ItemInterativo(
                            estado.get("nome", "item"),
                            estado.get("x", 0),
                            estado.get("y", 0),
                            estado.get("descricao", ""),
                            raio=estado.get("raio", 46),
                            tipo_sprite=estado.get("tipo_sprite"),
                        )
                        for campo, valor_item in estado.items():
                            with suppress(Exception):
                                setattr(item, campo, valor_item)

                        return item

                return {"__object_state__": estado, "__object_type__": tipo}
            return {k: self._resolver_valor(v, entidades) for k, v in valor.items()}
        if isinstance(valor, list):
            return [self._resolver_valor(x, entidades) for x in valor]
        return valor

    def _aplicar_estado_objeto(self, objeto, estado):
        if objeto is None or not isinstance(estado, dict):
            return
        for nome, valor in estado.items():
            with suppress(Exception):
                setattr(objeto, nome, valor)

    def _aplicar_controlador(self, estado_salvo, entidades):
        cc = getattr(self.cenario, "conversa_controller", None)
        if cc is None:
            return
        objetos_pendentes = []
        for nome, valor in estado_salvo.items():
            if nome in {
                "cenario",
                "renderer",
                "recolher_bernardo",
                "evolucao",
                "_movimento_roubao",
            }:
                continue

            if nome == "construir_casa":
                if isinstance(valor, dict) and "__object_state__" in valor:
                    objetos_pendentes.append(
                        (
                            nome,
                            self._resolver_valor(valor["__object_state__"], entidades),
                        )
                    )
                continue

            resolvido = self._resolver_valor(valor, entidades)
            if isinstance(resolvido, dict) and "__object_state__" in resolvido:
                objetos_pendentes.append((nome, resolvido["__object_state__"]))
                continue
            with suppress(Exception):
                setattr(cc, nome, resolvido)

        for nome, estado in objetos_pendentes:
            objeto = getattr(cc, nome, None)
            if nome == "construir_casa" and (
                objeto is None or isinstance(objeto, dict)
            ):
                try:
                    from application.usecases.aldeao.construir_casa import (
                        ConstruirCasaUseCase,
                    )

                    objeto = ConstruirCasaUseCase(self.cenario)
                    setattr(cc, nome, objeto)
                except Exception:
                    objeto = None
            if objeto is not None and isinstance(estado, dict):
                self._aplicar_estado_objeto(objeto, estado)

        construir = getattr(cc, "construir_casa", None)
        if construir is not None and hasattr(cc, "_casa_construida"):
            with suppress(Exception):
                construir.concluida_callback = cc._casa_construida

        if (
            construir is not None
            and getattr(construir, "ativo", False)
            and getattr(cc, "casa_fase", None) == "construindo"
        ):
            bernardo = getattr(cc, "bernardo", None) or getattr(
                construir, "bernardo", None
            )
            casa = getattr(cc, "casa_construindo", None) or getattr(
                construir, "casa", None
            )
            ponto = getattr(cc, "casa_ponto_entrega", None) or getattr(
                construir, "ponto", None
            )
            with suppress(Exception):
                retomar = getattr(construir, "retomar", None)
                if callable(retomar):
                    retomar(
                        bernardo=bernardo,
                        casa=casa,
                        ponto_entrega=ponto,
                        quantidade_madeira=getattr(construir, "madeira_restante", 0),
                        tempo=getattr(construir, "tempo", 0.0),
                        flip=getattr(construir, "flip", False),
                    )

    def _carregar_legacy_controlador(self, dados):
        cc = getattr(self.cenario, "conversa_controller", None)
        if cc is None:
            return
        conv = dados.get("conversa", {})
        if not conv:
            return
        mapa = {
            "estado": "estado",
            "inventario": "inventario",
            "bandidos_derrotados": "bandidos_derrotados",
            "casa_fase": "casa_fase",
            "casa_madeira_entregue": "casa_madeira_entregue",
            "casa_madeira_para_transportar": "casa_madeira_para_transportar",
            "cobras_derrotadas": "cobras_derrotadas",
            "martelo_recebido_por_bernardo": "martelo_recebido_por_bernardo",
        }
        for origem, destino in mapa.items():
            if origem in conv:
                setattr(cc, destino, conv[origem])
        if "casa_posicao" in conv:
            cc.casa_posicao = (
                tuple(conv["casa_posicao"])
                if conv["casa_posicao"] is not None
                else None
            )
        if "casa_ponto_entrega" in conv:
            cc.casa_ponto_entrega = (
                tuple(conv["casa_ponto_entrega"])
                if conv["casa_ponto_entrega"] is not None
                else None
            )
        cc._machado_spawnado = bool(conv.get("machado_spawnado", False))
        cc._roubao_dialogo_iniciado = bool(conv.get("dialogo_roubao_iniciado", False))
        cc._roubao_retorno_iniciado = bool(conv.get("roubao_retorno_iniciado", False))
        cc._roubao_saida_ativa = bool(conv.get("roubao_saida_ativa", False))

    def _aplicar_world_state(self, snapshot):
        """Restaura o estado temporal mutável do mundo sem conhecer missões."""
        if not snapshot:
            return
        context = getattr(self.cenario, "world_context", None)
        state = getattr(context, "state", None) if context is not None else None
        if state is None:
            return
        with suppress(Exception):
            from core.world.state import (
                Clima,
                EstadoAmeaca,
                EstadoFauna,
                EstadoRecurso,
                FaseDia,
                WorldEvent,
            )

            state.tempo_simulado = float(
                snapshot.get("tempo_simulado", state.tempo_simulado)
            )
            state.fase = FaseDia(str(snapshot.get("fase", state.fase.value)))
            state.clima = Clima(str(snapshot.get("clima", state.clima.value)))
            state.eventos_habilitados = bool(
                snapshot.get("eventos_habilitados", state.eventos_habilitados)
            )
            state.recursos = {
                k: EstadoRecurso(str(v))
                for k, v in snapshot.get("recursos", {}).items()
            }
            state.temporizadores_recursos = {
                k: float(v)
                for k, v in snapshot.get("temporizadores_recursos", {}).items()
            }
            state.fauna = {
                k: EstadoFauna(str(v)) for k, v in snapshot.get("fauna", {}).items()
            }
            state.ameacas = {
                k: EstadoAmeaca(str(v)) for k, v in snapshot.get("ameacas", {}).items()
            }
            state.eventos = {
                k: WorldEvent(
                    k,
                    v.get("tipo", ""),
                    float(v.get("duracao", 0)),
                    float(v.get("restante", 0)),
                    v.get("regiao"),
                )
                for k, v in snapshot.get("eventos", {}).items()
            }
            state._tempo_clima = float(snapshot.get("tempo_clima", state._tempo_clima))
            state._recursos_regenerados.clear()

    def _restaurar_descanso_sapudo(self, estado):
        c = self.cenario
        if not isinstance(estado, dict):
            return
        c._descanso_sapudo_fator_relogio = float(
            estado.get(
                "fator_relogio", getattr(c, "_descanso_sapudo_fator_relogio", 180.0)
            )
        )
        c._descanso_sapudo_ativo = bool(estado.get("ativo", False))
        posicao = estado.get("posicao")
        if isinstance(posicao, (list, tuple)) and len(posicao) >= 2:
            try:
                c._descanso_sapudo_posicao = (
                    float(posicao[0]),
                    float(posicao[1]),
                    int(posicao[2])
                    if len(posicao) >= 3
                    else int(getattr(c.sapudo, "altura", 0)),
                )
            except Exception:
                c._descanso_sapudo_posicao = None
        else:
            c._descanso_sapudo_posicao = None

        sapudo = getattr(c, "sapudo", None)
        if c._descanso_sapudo_ativo and sapudo is not None:
            sapudo.visivel = False
            sapudo.destino_x = sapudo.x
            sapudo.destino_y = sapudo.y

    def _restaurar_recolher_bernardo(self, estado):
        c = self.cenario
        cc = getattr(c, "conversa_controller", None)
        usecase = getattr(cc, "recolher_bernardo", None) if cc is not None else None
        if usecase is None or not isinstance(estado, dict):
            return

        usecase.ativo = bool(estado.get("ativo", False))
        usecase.dormindo = bool(estado.get("dormindo", False))
        usecase.voltando_para_inicio = bool(estado.get("voltando_para_inicio", False))
        usecase.destino = self._ponto_estado(estado.get("destino"))
        usecase.destino_inicial = self._ponto_estado(estado.get("destino_inicial"))
        usecase.tipo_destino = estado.get("tipo_destino")

        bernardo = getattr(cc, "bernardo", None)
        if bernardo is None:
            return
        if usecase.dormindo:
            bernardo.visivel = False
            bernardo.destino_x = bernardo.x
            bernardo.destino_y = bernardo.y
        elif usecase.voltando_para_inicio:
            bernardo.visivel = True
            if usecase.destino is not None:
                bernardo.destino_x, bernardo.destino_y = usecase.destino

    @staticmethod
    def _ponto_estado(valor):
        if valor is None:
            return None
        try:
            return (float(valor[0]), float(valor[1]))
        except Exception:
            return None

    def carregar(self):
        try:
            if not SAVE_PATH.exists():
                self.ultimo_status = "Nenhum save encontrado"
                return False

            dados = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
            c = self.cenario
            c._carregando_save = True
            registros = list(dados.get("entidades", []))
            versao = int(dados.get("version", 1))
            ids_salvos = {
                self._id_registro(r, i, versao) for i, r in enumerate(registros)
            }

            c.ciclo_dia_noite.definir_hora(
                float(dados.get("ciclo", {}).get("hora", 8.0))
            )
            c.estoque = dict(dados.get("estoque", c.estoque))
            self._aplicar_world_state(dados.get("world_state"))

            self._restaurar_descanso_sapudo(dados.get("descanso_sapudo"))
            self._remover_dinamicas_fora_do_save(ids_salvos)
            c._entidades_save_detached = {}
            self._recriar_dinamicas_salvas(registros, versao)

            estado_controlador_salvo = dados.get("controlador_estado", {})
            estado_controlador_salvo = self._migrar_referencias_legadas(
                estado_controlador_salvo
            )

            entidades = self._indice_entidades()
            for registro in registros:
                entidade = entidades.get(str(registro.get("save_id")))
                if entidade is None:
                    nome = registro.get("nome")
                    entidade = next(
                        (
                            e
                            for e in self._todas_entidades()
                            if getattr(e, "nome", None) == nome
                        ),
                        None,
                    )
                if entidade is not None:
                    self._aplicar_entidade(entidade, registro)
                    with suppress(Exception):
                        c.indice_espacial.atualizar(entidade)

            if "controlador_estado" in dados:
                self._aplicar_controlador(
                    estado_controlador_salvo, self._indice_entidades()
                )
            else:
                self._carregar_legacy_controlador(dados)

            self._restaurar_itens_interativos(dados)
            self._normalizar_itens_interativos_controlador()

            cam = dados.get("camera", {})
            c.camera.x = float(cam.get("x", c.camera.x))
            c.camera.y = float(cam.get("y", c.camera.y))

            c.bandidos_inicializados = True
            self._sincronizar_referencias_pós_load()
            self._restaurar_recolher_bernardo(dados.get("recolher_bernardo"))
            self._retomar_construcao_no_final_do_load()
            self._restaurar_retorno_caverna_urso(dados.get("retorno_caverna_urso"))
            if not getattr(c, "_urso_retornando_caverna", False):
                self._restaurar_perseguicao_urso(dados.get("perseguicao_urso"))

            self.ultimo_status = "Jogo carregado"
            c._carregando_save = False
            return True
        except Exception as exc:
            with suppress(Exception):
                self.cenario._carregando_save = False
            self.ultimo_status = f"Erro ao carregar: {str(exc)[:36]}"
            return False

    def _restaurar_itens_interativos(self, dados):
        with suppress(Exception):
            from domains.interacao_item import ItemInterativo

            c = self.cenario
            c.itens_interativos[:] = []
            for item in dados.get("itens_interativos", []):
                c.itens_interativos.append(
                    ItemInterativo(
                        item.get("nome", "item"),
                        item.get("x", 0),
                        item.get("y", 0),
                        item.get("descricao", ""),
                        raio=item.get("raio", 46),
                        tipo_sprite=item.get("tipo_sprite"),
                    )
                )
            cc = getattr(c, "conversa_controller", None)
            if cc is not None:
                for item in c.itens_interativos:
                    if getattr(item, "nome", None) == "machado":
                        cc.machado = item
                    elif getattr(item, "nome", None) == "martelo":
                        cc.martelo = item

    def _normalizar_itens_interativos_controlador(self):
        cc = getattr(self.cenario, "conversa_controller", None)
        if cc is None:
            return
        try:
            from domains.interacao_item import ItemInterativo
        except Exception:
            return

        for nome in ("machado", "martelo"):
            valor = getattr(cc, nome, None)
            if isinstance(valor, ItemInterativo):
                continue
            estado = None
            if isinstance(valor, dict):
                if "__item_interativo__" in valor:
                    estado = valor.get("__item_interativo__")
                elif "__object_state__" in valor:
                    estado = valor.get("__object_state__")
                elif {"nome", "x", "y"}.issubset(valor):
                    estado = valor
            if not isinstance(estado, dict):
                continue
            item = ItemInterativo(
                estado.get("nome", nome),
                estado.get("x", 0),
                estado.get("y", 0),
                estado.get("descricao", ""),
                raio=estado.get("raio", 46),
                tipo_sprite=estado.get("tipo_sprite"),
            )
            item.coletado = bool(estado.get("coletado", False))
            setattr(cc, nome, item)
            itens = getattr(self.cenario, "itens_interativos", None)
            if itens is not None and item not in itens and not item.coletado:
                itens.append(item)

    def _sincronizar_referencias_pós_load(self):
        """Recria referências de runtime sem redefinir progresso."""
        c = self.cenario
        cc = getattr(c, "conversa_controller", None)
        if cc is None:
            return

        if getattr(cc, "bernardo", None) is None:
            for entidade in getattr(c, "personagens", ()):
                if getattr(entidade, "nome", None) == "aldeao":
                    cc.bernardo = entidade
                    break

        casa = getattr(cc, "casa_construindo", None)
        fase_casa = getattr(cc, "casa_fase", None)
        if (
            casa is not None
            and getattr(casa, "nome", None)
            and fase_casa in {"indo_casa", "casa_construindo", "aguardando_martelo"}
        ):
            with suppress(Exception):
                construcoes = getattr(c, "construcoes", None)
                if construcoes is not None and casa not in construcoes:
                    c.adicionar_personagem(casa, "construcoes")
                c._entidades_save_detached.pop(str(getattr(casa, "save_id", "")), None)
                casa.proprietario_bernardo = True
                casa.visivel = True
                garantir = getattr(cc, "_garantir_casa_construindo_visivel", None)
                if callable(garantir):
                    garantir()

        indice = self._indice_entidades()
        entidades_validas = set(id(item) for item in indice.values())
        for nome, valor in list(vars(cc).items()):
            if isinstance(valor, list):
                filtrado = [
                    item
                    for item in valor
                    if item is None or id(item) in entidades_validas
                ]
                if len(filtrado) != len(valor):
                    setattr(cc, nome, filtrado)

    def _retomar_construcao_no_final_do_load(self):
        c = self.cenario
        cc = getattr(c, "conversa_controller", None)
        if cc is None:
            return
        construir = getattr(cc, "construir_casa", None)
        if construir is None:
            return
        if not getattr(construir, "ativo", False):
            return
        if getattr(cc, "casa_fase", None) != "construindo":
            return

        bernardo = getattr(cc, "bernardo", None) or getattr(construir, "bernardo", None)
        casa = getattr(cc, "casa_construindo", None) or getattr(construir, "casa", None)
        ponto = getattr(cc, "casa_ponto_entrega", None) or getattr(
            construir, "ponto", None
        )
        if bernardo is None or casa is None or ponto is None:
            return

        try:
            construir.concluida_callback = cc._casa_construida
            construir.retomar(
                bernardo=bernardo,
                casa=casa,
                ponto_entrega=ponto,
                quantidade_madeira=getattr(construir, "madeira_restante", 0),
                tempo=getattr(construir, "tempo", 0.0),
                flip=getattr(construir, "flip", False),
            )
        except Exception:
            return

    def salvar(self):
        try:
            SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            SAVE_PATH.write_text(
                json.dumps(self._coletar(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.ultimo_status = "Jogo salvo"
            return True
        except Exception as exc:
            self.ultimo_status = f"Erro ao salvar: {str(exc)[:36]}"
            return False
