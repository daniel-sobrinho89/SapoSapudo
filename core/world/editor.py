from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

from core.world.model import Position, Region, WorldSpawn
from utils.config import TILE_SIZE


class WorldEditor:
    """Editor visual/runtime do World Model.

    A mesma camada atende a UI do F4 e a ferramenta CLI legada. O editor
    modifica o WorldModel em memória, permite salvar de forma atômica e
    reindexa os serviços do contexto sem criar um segundo mundo.
    """

    MODOS = ("regiao", "objeto", "terreno")
    PAPEIS = (
        "generica",
        "hub_inicial",
        "coleta_recorrente",
        "recurso_avancado",
        "narrativa_ambiental",
        "threat_poi",
        "transicao",
        "fronteira_aquatica",
    )
    RISCOS = ("baixo", "medio", "medio_alto", "alto")

    def __init__(self, world_service):
        self.world_service = world_service
        self.ativo = False
        self.modo = "regiao"
        self.selecao = None
        self.arrastando = False
        self._drag_origin = None
        self._drag_value = None
        self.dirty = False
        self.status = "Editor pronto"
        self.tipo_objeto = "arvore1"
        self.tipo_terreno = "grama"
        self.submodo_terreno = "pincel"
        self.altura_relevo = 1
        self.colunas_relevo = 1
        self.linhas_relevo = 1
        self.colunas_por_linha_relevo = [1]
        self.linha_relevo_editando = 0
        self.relevo_selecionado_id = None
        self._area_inicio = None
        self._area_atual = None
        self._focar_callback = None
        self._adicionar_spawn_callback = None
        self._remover_spawn_callback = None
        self._mover_spawn_callback = None
        self.camera_anterior = None

    @property
    def context(self):
        return self.world_service.context

    @property
    def world(self):
        return self.context.world if self.context else None

    def configurar_callbacks(
        self, focar=None, adicionar_spawn=None, remover_spawn=None, mover_spawn=None
    ):
        self._focar_callback = focar
        self._adicionar_spawn_callback = adicionar_spawn
        self._remover_spawn_callback = remover_spawn
        self._mover_spawn_callback = mover_spawn

    def alternar(self) -> bool:
        self.ativo = not self.ativo
        self.status = "Editor visual ativo" if self.ativo else "Editor visual fechado"
        if self.ativo:
            self.selecao = None
        return self.ativo

    @property
    def tipos_objeto(self):
        return (
            "arvore1",
            "arvore2",
            "arvore3",
            "arvore4",
            "arbusto1",
            "arbusto2",
            "arbusto3",
            "arbusto4",
            "pedra1",
            "pedra2",
            "pedra3",
            "pedra4",
            "pedra_agua1",
            "pedra_agua2",
            "pedra_agua3",
            "pedra_agua4",
            "mina_ouro",
            "osso1",
            "osso2",
            "osso3",
            "ovelha",
        )

    def iniciar_area(self, coluna, linha):
        if self.context is None:
            return False
        coluna = int(coluna)
        linha = int(linha)
        if not (
            0 <= coluna < self.context.validator.colunas
            and 0 <= linha < self.context.validator.linhas
        ):
            return False

        # No modo RELEVO, um clique sobre uma célula já pertencente a um
        # relevo existente deve sempre selecionar esse relevo. Nunca criamos
        # outro relevo sobre uma geometria já existente.
        if self.modo == "terreno" and self.submodo_terreno == "relevo":
            existente = self.selecionar_relevo_por_tile(coluna, linha)
            if existente is not None:
                self.arrastando = False
                self._area_inicio = None
                self._area_atual = None
                return True

        self._area_inicio = (coluna, linha)
        self._area_atual = self._area_inicio
        self.arrastando = True
        self.status = "Definindo área..."
        return True

    def atualizar_area(self, coluna, linha):
        if not self.arrastando or self._area_inicio is None:
            return False
        coluna = max(0, min(self.context.validator.colunas - 1, int(coluna)))
        linha = max(0, min(self.context.validator.linhas - 1, int(linha)))
        self._area_atual = (coluna, linha)
        return True

    def finalizar_area(self):
        if not self.arrastando or self._area_inicio is None or self._area_atual is None:
            return False
        c0, l0 = self._area_inicio
        c1, l1 = self._area_atual
        if self.submodo_terreno == "relevo":
            # As dimensões configuradas no editor são a fonte da verdade do
            # relevo. O clique define somente a origem.
            x, y = c0, l0
            colunas, linhas = self.colunas_relevo, self.linhas_relevo
        else:
            x, y = min(c0, c1), min(l0, l1)
            colunas, linhas = abs(c1 - c0) + 1, abs(l1 - l0) + 1
        self.arrastando = False
        self._area_inicio = None
        self._area_atual = None
        if self.modo == "terreno":
            if self.submodo_terreno == "relevo":
                return self.adicionar_relevo(x, y, colunas, linhas)
            if self.submodo_terreno == "espuma":
                return self.adicionar_espuma(x, y, colunas, linhas)
        return False

    def preview_area(self):
        if self._area_inicio is None or self._area_atual is None:
            return None
        c0, l0 = self._area_inicio
        c1, l1 = self._area_atual
        if self.submodo_terreno == "relevo":
            return (c0, l0, self.colunas_relevo, self.linhas_relevo)
        return (min(c0, c1), min(l0, l1), abs(c1 - c0) + 1, abs(l1 - l0) + 1)

    def adicionar_relevo(self, x, y, colunas, linhas):
        renderer = (
            getattr(self.context, "tilemap_renderer", None) if self.context else None
        )
        if renderer is None:
            return False
        if any(
            renderer.obter_tipo(c, lin) != renderer.TIPO_GRAMA
            for lin in range(y, y + linhas)
            for c in range(x, x + colunas)
        ):
            self.status = "Relevo deve ser criado sobre terreno de grama"
            return False

        for relevo in getattr(renderer, "_relevos_config", ()):
            for segmento in relevo.get("forma", ()):
                rx = int(segmento.get("x", 0))
                ry = int(segmento.get("y", 0))
                rcols = max(1, int(segmento.get("colunas", 1)))
                if not (
                    x + colunas <= rx
                    or rx + rcols <= x
                    or y + linhas <= ry
                    or ry + 1 <= y
                ):
                    self.selecionar_relevo_por_tile(rx, ry)
                    self.status = f"Relevo {relevo.get('id')} já existe nesta área"
                    return True

        colunas_por_linha = list(self.colunas_por_linha_relevo)
        if len(colunas_por_linha) != int(linhas):
            ultimo = colunas_por_linha[-1] if colunas_por_linha else int(colunas)
            colunas_por_linha = (colunas_por_linha + [ultimo] * int(linhas))[
                : int(linhas)
            ]
        relevo_id = renderer.adicionar_relevo_editor(
            int(x),
            int(y),
            int(colunas),
            int(linhas),
            altura=self.altura_relevo,
            colunas_por_linha=colunas_por_linha,
        )
        if relevo_id is None:
            self.status = "Não foi possível criar o relevo"
            return False
        self.dirty = True
        self.status = f"Relevo {relevo_id} criado. Clique em SALVAR."
        return True

    def adicionar_espuma(self, x, y, colunas, linhas):
        renderer = (
            getattr(self.context, "tilemap_renderer", None) if self.context else None
        )
        if renderer is None:
            return False

        # adjacente à água.
        celulas = [
            (c, lin) for lin in range(y, y + linhas) for c in range(x, x + colunas)
        ]
        if not celulas or any(
            not renderer._coordenada_valida(c, lin) for c, lin in celulas
        ):
            self.status = "Área de espuma fora do mapa"
            return False

        def toca_agua(c, lin):
            if renderer.obter_tipo(c, lin) == renderer.TIPO_AGUA_FUNDO:
                return True
            return any(
                renderer.obter_tipo(nc, nl) == renderer.TIPO_AGUA_FUNDO
                for nc, nl in ((c - 1, lin), (c + 1, lin), (c, lin - 1), (c, lin + 1))
                if renderer._coordenada_valida(nc, nl)
            )

        if not all(toca_agua(c, lin) for c, lin in celulas):
            self.status = "Espuma deve ficar sobre água ou na borda imediata da água"
            return False
        espuma_id = renderer.adicionar_espuma_editor(x, y, colunas, linhas)
        if espuma_id is None:
            self.status = "A espuma precisa tocar uma célula de água."
            return False
        self.dirty = True
        self.status = f"Espuma {espuma_id} criada na borda da água. Clique em SALVAR."
        return True

    @staticmethod
    def _bbox_relevo(relevo):
        forma = list(relevo.get("forma", ()))
        if not forma and "x" in relevo and "y" in relevo:
            return (
                int(relevo.get("x", 0)),
                int(relevo.get("y", 0)),
                max(1, int(relevo.get("colunas", 1))),
                max(1, int(relevo.get("linhas", 1))),
            )
        if not forma:
            return 0, 0, 1, 1
        x0 = min(int(seg.get("x", 0)) for seg in forma)
        y0 = min(int(seg.get("y", 0)) for seg in forma)
        x1 = max(
            int(seg.get("x", 0)) + max(1, int(seg.get("colunas", 1))) - 1
            for seg in forma
        )
        y1 = max(int(seg.get("y", 0)) for seg in forma)
        return x0, y0, x1 - x0 + 1, y1 - y0 + 1

    def selecionar_relevo_por_tile(self, coluna: int, linha: int):
        renderer = (
            getattr(self.context, "tilemap_renderer", None) if self.context else None
        )

        if renderer is None:
            return None

        for relevo in getattr(renderer, "_relevos_config", ()):
            segmentos = list(relevo.get("forma", ()))

            if not segmentos and "x" in relevo and "y" in relevo:
                segmentos = [
                    {
                        "x": relevo.get("x", 0),
                        "y": relevo.get("y", 0),
                        "colunas": relevo.get("colunas", 1),
                    }
                ]

            dentro_forma = False

            for segmento in segmentos:
                rx = int(segmento.get("x", 0))
                ry = int(segmento.get("y", 0))
                cols = max(1, int(segmento.get("colunas", 1)))

                if rx <= int(coluna) < rx + cols and ry == int(linha):
                    dentro_forma = True
                    break

            dentro_render = False

            for segmento in getattr(renderer, "_relevos_segmentos", ()):
                if int(segmento.get("id", -1)) != int(relevo.get("id", -2)):
                    continue

                rx = int(segmento.get("x", 0))
                ry = int(segmento.get("y", 0))
                cols = max(1, int(segmento.get("colunas", 1)))
                linhas = max(1, int(segmento.get("linhas", 1)))

                if (
                    rx <= int(coluna) < rx + cols
                    and ry + 1 <= int(linha) <= ry + linhas
                ):
                    dentro_render = True
                    break

            if dentro_forma or dentro_render:
                bx, by, bcols, blinhas = self._bbox_relevo(relevo)

                self.relevo_selecionado_id = relevo.get("id")
                self.colunas_relevo = bcols
                self.linhas_relevo = blinhas
                self.altura_relevo = int(relevo.get("altura", 1))

                self.colunas_por_linha_relevo = [
                    max(1, int(seg.get("colunas", bcols)))
                    for seg in sorted(
                        segmentos,
                        key=lambda seg: int(seg.get("y", 0)),
                    )
                ]

                if not self.colunas_por_linha_relevo:
                    self.colunas_por_linha_relevo = [bcols] * blinhas

                self.linha_relevo_editando = min(
                    self.linha_relevo_editando,
                    len(self.colunas_por_linha_relevo) - 1,
                )

                self.selecao = {
                    "id": relevo.get("id"),
                    "tile": (bx, by),
                    "relevo": True,
                }

                self.status = f"Relevo {relevo.get('id')} selecionado"

                if self._focar_callback:
                    self._focar_callback(
                        {
                            "x": bx,
                            "y": by,
                            "colunas": bcols,
                            "linhas": blinhas,
                            "id": relevo.get("id"),
                        }
                    )

                return relevo

        return None

    def selecionar_tipo_objeto(self, tipo):
        if tipo in self.tipos_objeto:
            self.tipo_objeto = tipo
            self.status = f"Pincel: {tipo}"
            return True
        return False

    def selecionar_tipo_terreno(self, tipo):
        if tipo in ("grama", "agua_fundo"):
            self.tipo_terreno = tipo
            self.submodo_terreno = "pincel"
            self.modo = "terreno"
            self.relevo_selecionado_id = None
            self.selecao = None
            self.status = f"Terreno: {tipo}"
            return True
        if tipo in ("relevo", "espuma"):
            self.submodo_terreno = tipo
            self.modo = "terreno"
            if tipo != "relevo":
                self.relevo_selecionado_id = None
                self.selecao = None
            self.status = f"Terreno: {tipo}"
            return True
        return False

    def _sincronizar_colunas_por_linha(
        self, linhas: int, valor_padrao: int | None = None
    ):
        linhas = max(1, int(linhas))
        atual = list(self.colunas_por_linha_relevo or [])
        padrao = max(
            1,
            int(
                valor_padrao
                if valor_padrao is not None
                else (atual[-1] if atual else self.colunas_relevo)
            ),
        )
        atual = (atual + [padrao] * linhas)[:linhas]
        self.colunas_por_linha_relevo = [max(1, int(v)) for v in atual]
        self.linhas_relevo = linhas
        self.colunas_relevo = max(self.colunas_por_linha_relevo, default=1)
        self.linha_relevo_editando = min(self.linha_relevo_editando, linhas - 1)

    def _aplicar_forma_relevo_selecionado(self) -> bool:
        renderer = (
            getattr(self.context, "tilemap_renderer", None) if self.context else None
        )
        if renderer is None or self.relevo_selecionado_id is None:
            return False
        alvo = next(
            (
                r
                for r in renderer._relevos_config
                if int(r.get("id", -1)) == int(self.relevo_selecionado_id)
            ),
            None,
        )
        if alvo is None:
            return False
        bx, by, _, _ = self._bbox_relevo(alvo)
        if by + len(self.colunas_por_linha_relevo) > renderer.altura:
            self.status = "Dimensão do relevo ultrapassa o mapa"
            return False
        if any(
            bx + max(1, int(cols)) > renderer.largura
            for cols in self.colunas_por_linha_relevo
        ):
            self.status = "Uma das linhas do relevo ultrapassa o mapa"
            return False
        alvo["forma"] = [
            {"y": by + linha, "x": bx, "colunas": max(1, int(cols))}
            for linha, cols in enumerate(self.colunas_por_linha_relevo)
        ]
        alvo["altura"] = int(self.altura_relevo)
        renderer._reindexar_camadas_editor()
        self.linhas_relevo = len(self.colunas_por_linha_relevo)
        self.colunas_relevo = max(self.colunas_por_linha_relevo)
        self.selecao["tile"] = (bx, by)
        self.dirty = True
        self.status = f"Relevo {alvo.get('id')} atualizado"
        return True

    def alterar_colunas_linha(self, delta: int) -> bool:
        if not self.context or not self.colunas_por_linha_relevo:
            return False
        indice = min(
            max(0, int(self.linha_relevo_editando)),
            len(self.colunas_por_linha_relevo) - 1,
        )
        limite = self.context.validator.colunas
        atual = self.colunas_por_linha_relevo[indice]
        novo = max(1, min(limite, int(atual) + int(delta)))
        self.colunas_por_linha_relevo[indice] = novo
        self.colunas_relevo = max(self.colunas_por_linha_relevo)
        if self.relevo_selecionado_id is None:
            self.status = f"Linha {indice + 1}: {novo} colunas"
            return True
        return self._aplicar_forma_relevo_selecionado()

    def selecionar_linha_relevo(self, indice: int) -> bool:
        if not self.colunas_por_linha_relevo:
            return False
        self.linha_relevo_editando = min(
            max(0, int(indice)), len(self.colunas_por_linha_relevo) - 1
        )
        cols = self.colunas_por_linha_relevo[self.linha_relevo_editando]
        self.colunas_relevo = max(self.colunas_por_linha_relevo)
        self.status = f"Editando linha {self.linha_relevo_editando + 1}: {cols} colunas"
        return True

    def alterar_dimensao_relevo(self, eixo: str, delta: int) -> bool:
        if eixo not in ("colunas", "linhas") or not self.context:
            return False
        if eixo == "colunas":
            return self.alterar_colunas_linha(delta)

        limite = self.context.validator.linhas
        novo = max(1, min(limite, self.linhas_relevo + int(delta)))
        if novo == self.linhas_relevo:
            return True
        if novo > self.linhas_relevo:
            valor = (
                self.colunas_por_linha_relevo[-1]
                if self.colunas_por_linha_relevo
                else 1
            )
            self.colunas_por_linha_relevo.append(max(1, int(valor)))
        else:
            self.colunas_por_linha_relevo = self.colunas_por_linha_relevo[:novo]
        self.linhas_relevo = novo
        self.linha_relevo_editando = min(self.linha_relevo_editando, novo - 1)
        self.colunas_relevo = max(self.colunas_por_linha_relevo, default=1)
        if self.relevo_selecionado_id is None:
            self.status = f"Relevo: {novo} linhas"
            return True
        return self._aplicar_forma_relevo_selecionado()

    def remover_relevo_selecionado(self) -> bool:
        if not self.context or self.relevo_selecionado_id is None:
            return False
        renderer = getattr(self.context, "tilemap_renderer", None)
        if renderer is None:
            return False
        alvo_id = int(self.relevo_selecionado_id)
        antes = len(renderer._relevos_config)
        renderer._relevos_config = [
            r for r in renderer._relevos_config if int(r.get("id", -1)) != alvo_id
        ]
        if len(renderer._relevos_config) == antes:
            return False
        renderer._reindexar_camadas_editor()
        self.relevo_selecionado_id = None
        self.selecao = None
        self.colunas_por_linha_relevo = [1]
        self.colunas_relevo = 1
        self.linhas_relevo = 1
        self.linha_relevo_editando = 0
        self.dirty = True
        self.status = f"Relevo {alvo_id} removido. Clique em SALVAR."
        return True

    def definir_modo(self, modo: str) -> None:
        if modo in self.MODOS:
            self.modo = modo
            self.selecao = None
            self.status = f"Modo: {modo}"

    def selecionar(self, x: float, y: float):
        context = self.context
        if context is None:
            return None
        coluna, linha = context._pixel_para_tile(x, y)
        regiao = context.region_service.no_tile(coluna, linha)

        objeto = None
        if self.modo == "terreno" and self.submodo_terreno == "relevo":
            relevo = self.selecionar_relevo_por_tile(coluna, linha)
            if relevo is not None:
                return self.selecao
        if self.modo == "regiao":
            objeto = regiao
        elif self.modo == "objeto":
            spawn = self.spawn_no_tile(coluna, linha)
            if spawn is not None:
                self.selecao = {"id": spawn.id, "tile": (coluna, linha), "spawn": True}
                self.status = f"Selecionado: {spawn.tipo}"
                return self.selecao
            self.selecao = {"id": None, "tile": (coluna, linha), "spawn": False}
            return self.selecao

        self.selecao = {
            "tile": (coluna, linha),
            "regiao": regiao.id if regiao else None,
            "id": getattr(objeto, "id", None),
        }
        self.status = (
            f"Selecionado: {self.selecao['id']}"
            if self.selecao["id"]
            else "Nenhum objeto no ponto"
        )
        if objeto is not None and self._focar_callback:
            self._focar_callback(objeto)
        return self.selecao

    def spawns_visuais(self):
        if self.world is None:
            return ()
        return tuple(self.world.spawns.values())

    def spawn_no_tile(self, coluna: int, linha: int):
        candidatos = []
        runtime = (
            getattr(self.context, "_entidades_runtime", {}) if self.context else {}
        )
        for spawn in self.spawns_visuais():
            entidade = runtime.get(spawn.id)
            px = getattr(entidade, "x", spawn.posicao.x)
            py = getattr(entidade, "y", spawn.posicao.y)
            c, lin = self.context._pixel_para_tile(px, py)
            if c == coluna and lin == linha:
                candidatos.append(spawn)
        return candidatos[0] if candidatos else None

    def descricao_spawn(self):
        if not self.selecao or not self.selecao.get("spawn") or self.world is None:
            return {}
        spawn = self.world.spawns.get(self.selecao.get("id"))
        if not spawn:
            return {}
        return {
            "tipo": "Objeto",
            "id": spawn.id,
            "objeto": spawn.tipo,
            "regiao": spawn.regiao or "-",
            "x": int(spawn.posicao.x),
            "y": int(spawn.posicao.y),
            "origem": spawn.origem,
        }

    def adicionar_objeto_no_tile(self, coluna, linha):
        if self.world is None or self.context is None:
            return False
        if not (
            0 <= coluna < self.context.validator.colunas
            and 0 <= linha < self.context.validator.linhas
        ):
            return False
        existente = self.spawn_no_tile(coluna, linha)
        if existente is not None:
            self.selecao = {"id": existente.id, "tile": (coluna, linha), "spawn": True}
            self.status = f"Selecionado: {existente.tipo}"
            return False
        regiao = self.context.region_service.no_tile(coluna, linha)
        if regiao is None:
            self.status = "O objeto precisa estar em uma região"
            return False
        x, y = self.context.tilemap_renderer.tile_para_pixel(coluna, linha)
        spawn_id = self._novo_spawn_id(self.tipo_objeto, regiao.id)
        spawn = WorldSpawn(
            id=spawn_id,
            tipo=self.tipo_objeto,
            regiao=regiao.id,
            posicao=Position(
                x + TILE_SIZE / 2,
                y + TILE_SIZE / 2,
                self.context.tilemap_renderer.obter_altura(coluna, linha),
            ),
            tags=("editor",),
            origem="editor_visual",
        )
        self.world.spawns[spawn.id] = spawn
        self.context.reindexar()
        issues = self.context.validator.validar()
        self.context.validator.issues = tuple(issues)
        if any(
            i.severity == "ERROR" and i.location.startswith(spawn.id + "@")
            for i in issues
        ):
            self.world.spawns.pop(spawn.id, None)
            self.context.reindexar()
            self.status = f"{spawn.tipo} não pode ser colocado neste terreno"
            return False
        self.selecao = {"id": spawn.id, "tile": (coluna, linha), "spawn": True}
        self.dirty = True
        self.status = f"Adicionado: {spawn.tipo}. Clique em SALVAR."
        if self._adicionar_spawn_callback:
            self._adicionar_spawn_callback(spawn)
        return True

    def remover_selecionado(self):
        if not self.selecao or not self.selecao.get("spawn") or self.world is None:
            return False
        spawn_id = self.selecao.get("id")
        spawn = self.world.spawns.pop(spawn_id, None)
        if spawn is None:
            return False
        self.context.reindexar()
        if self._remover_spawn_callback:
            self._remover_spawn_callback(spawn)
        self.selecao = None
        self.dirty = True
        self.status = "Objeto removido. Clique em SALVAR."
        return True

    def pintar_terreno_no_tile(self, coluna, linha):
        if self.context is None:
            return False
        if not (
            0 <= coluna < self.context.validator.colunas
            and 0 <= linha < self.context.validator.linhas
        ):
            return False
        renderer = getattr(self.context, "tilemap_renderer", None)
        if renderer is None:
            return False
        renderer.definir_terreno_editor(coluna, linha, self.tipo_terreno)
        self.dirty = True
        self.status = f"Terreno {self.tipo_terreno} aplicado. Clique em SALVAR."
        return True

    def _novo_spawn_id(self, tipo, regiao):
        base = f"{tipo}_{regiao}_editor"
        idx = 1
        while f"{base}_{idx:03d}" in self.world.spawns:
            idx += 1
        return f"{base}_{idx:03d}"

    def selecionar_id(self, modo: str, item_id: str) -> bool:
        self.definir_modo(modo)
        if self.world is None:
            return False
        colecao = self.world.regions if modo == "regiao" else {}
        if item_id not in colecao:
            return False
        self.selecao = {"id": item_id, "tile": self._tile_do_objeto(colecao[item_id])}
        self._preencher_contexto_selecao(self.selecao["tile"])
        self.status = f"Selecionado: {item_id}"
        if self._focar_callback:
            self._focar_callback(colecao[item_id])
        return True

    def selecionar_spawn_id(self, item_id: str) -> bool:
        if self.world is None or item_id not in self.world.spawns:
            return False
        spawn = self.world.spawns[item_id]
        self.modo = "objeto"
        self.tipo_objeto = (
            spawn.tipo if spawn.tipo in self.tipos_objeto else self.tipo_objeto
        )
        tile = self.context._pixel_para_tile(spawn.posicao.x, spawn.posicao.y)
        self.selecao = {"id": item_id, "tile": tile, "spawn": True}
        self.status = f"Selecionado: {spawn.tipo}"
        if self._focar_callback:
            self._focar_callback(spawn)
        return True

    def descricao(self) -> dict:
        if not self.selecao or self.world is None:
            return {}
        item = self.item_selecionado()
        if item is None:
            return {}
        if isinstance(item, Region):
            return {
                "tipo": "Região",
                "id": item.id,
                "nome": item.nome,
                "papel": item.papel,
                "tier": item.tier,
                "risco": item.risco,
                "recompensa": item.recompensa or "-",
                "x": item.x,
                "y": item.y,
                "colunas": item.colunas,
                "linhas": item.linhas,
            }
        if self.modo == "objeto" and self.selecao and self.selecao.get("spawn"):
            return self.descricao_spawn()
        if (
            self.modo == "terreno"
            and self.relevo_selecionado_id is not None
            and isinstance(item, dict)
        ):
            return {
                "tipo": "Relevo",
                "id": item.get("id"),
                "altura": item.get("altura", 1),
                "colunas": self.colunas_relevo,
                "linhas": self.linhas_relevo,
                "x": self.selecao.get("tile", (0, 0))[0],
                "y": self.selecao.get("tile", (0, 0))[1],
            }
        return {}

    def item_selecionado(self):
        if not self.selecao or self.world is None:
            return None
        item_id = self.selecao.get("id")
        if not item_id:
            return None
        if self.modo == "objeto":
            return self.world.spawns.get(item_id)
        if self.modo == "terreno" and self.relevo_selecionado_id is not None:
            renderer = (
                getattr(self.context, "tilemap_renderer", None)
                if self.context
                else None
            )
            if renderer is not None:
                for relevo in renderer._relevos_config:
                    if int(relevo.get("id", -1)) == int(self.relevo_selecionado_id):
                        return relevo
            return None
        return self.world.regions.get(item_id) if self.modo == "regiao" else None

    def ponto_esta_no_selecionado(self, x: float, y: float) -> bool:
        item = self.item_selecionado()
        if item is None or self.context is None:
            return False
        coluna, linha = self.context._pixel_para_tile(x, y)
        if isinstance(item, Region):
            return item.contem_tile(coluna, linha)
        if isinstance(item, WorldSpawn):
            sx, sy = self.context._pixel_para_tile(item.posicao.x, item.posicao.y)
            return coluna == sx and linha == sy
        if (
            isinstance(item, dict)
            and self.modo == "terreno"
            and self.relevo_selecionado_id is not None
        ):
            bx, by, cols, linhas = self._bbox_relevo(item)
            return bx <= coluna < bx + cols and by <= linha < by + linhas
        return False

    def iniciar_arrasto(self, x: float, y: float) -> bool:
        item = self.item_selecionado()
        if item is None:
            return False
        context = self.context
        coluna, linha = context._pixel_para_tile(x, y)
        self.arrastando = True
        self._drag_origin = (coluna, linha)
        if isinstance(item, WorldSpawn):
            self._drag_value = self.context._pixel_para_tile(
                item.posicao.x, item.posicao.y
            )
        elif isinstance(item, Region):
            self._drag_value = (item.x, item.y)
        return True

    def mover_arrasto(self, x: float, y: float) -> bool:
        if not self.arrastando or self._drag_origin is None:
            return False
        context = self.context
        coluna, linha = context._pixel_para_tile(x, y)
        dx = coluna - self._drag_origin[0]
        dy = linha - self._drag_origin[1]
        item = self.item_selecionado()
        if item is None:
            return False

        if isinstance(item, WorldSpawn):
            col = int(self._drag_value[0] + dx)
            lin = int(self._drag_value[1] + dy)
            if (
                0 <= col < self.context.validator.colunas
                and 0 <= lin < self.context.validator.linhas
            ):
                x, y = self.context.tilemap_renderer.tile_para_pixel(col, lin)
                self.world.spawns[item.id] = replace(
                    item,
                    posicao=Position(
                        x + TILE_SIZE / 2, y + TILE_SIZE / 2, item.posicao.altura
                    ),
                )
                self.selecao["tile"] = (col, lin)
                self.context.reindexar()
                self.dirty = True
                if self._mover_spawn_callback:
                    self._mover_spawn_callback(
                        item,
                        (col, lin),
                    )
        elif isinstance(item, Region):
            self._substituir_regiao(
                item, x=int(self._drag_value[0] + dx), y=int(self._drag_value[1] + dy)
            )
        self.status = "Movendo..."
        return True

    def finalizar_arrasto(self) -> None:
        if self.arrastando:
            self.arrastando = False
            self._drag_origin = None
            self._drag_value = None
            self.status = "Alteração pendente. Clique em SALVAR."

    def alterar_propriedade(self, acao: str) -> bool:
        item = self.item_selecionado()
        if item is None:
            return False
        if isinstance(item, Region):
            if acao == "papel":
                self._substituir_regiao(
                    item, papel=self._proximo(self.PAPEIS, item.papel)
                )
            elif acao == "risco":
                self._substituir_regiao(
                    item, risco=self._proximo(self.RISCOS, item.risco)
                )
            elif acao == "tier_up":
                self._substituir_regiao(item, tier=min(5, item.tier + 1))
            elif acao == "tier_down":
                self._substituir_regiao(item, tier=max(0, item.tier - 1))
            elif acao == "recompensa":
                valores = (None, "madeira", "ouro", "carne", "exploracao")
                self._substituir_regiao(
                    item, recompensa=self._proximo(valores, item.recompensa)
                )
            else:
                return False
        self.context.reindexar()
        self.dirty = True
        self.status = "Alteração pendente. Clique em SALVAR."
        return True

    def atualizar_regiao(self, regiao_id: str, **campos) -> None:
        item = self.world.regions[regiao_id]
        self._substituir_regiao(item, **campos)
        self.salvar()

    def salvar(self) -> bool:
        ok = True
        try:
            self._salvar_regioes()
            self._salvar_spawns()
            if self.context and getattr(self.context, "tilemap_renderer", None):
                self.context.tilemap_renderer.salvar_terreno_editor()
            self.context.reindexar()
            self.dirty = False
            self.status = "Mundo salvo com sucesso"
        except Exception as exc:
            self.status = f"Erro ao salvar: {str(exc)[:28]}"
            ok = False
        return ok

    def _salvar_spawns(self):
        path = Path(self.world_service.world_dir) / "entities.json"
        backup = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup)
        dados = []
        for item in self.world.spawns.values():
            dados.append(
                {
                    "id": item.id,
                    "tipo": item.tipo,
                    "regiao": item.regiao,
                    "posicao": {
                        "x": item.posicao.x,
                        "y": item.posicao.y,
                        "altura": item.posicao.altura,
                    },
                    "tags": list(item.tags),
                    "origem": item.origem,
                }
            )
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temp.replace(path)

    def _salvar_regioes(self):
        self._salvar_colecao("regions.json", self.world.regions, self._region_json)

    def _substituir_regiao(self, item: Region, **changes):
        self.world.regions[item.id] = replace(item, **changes)
        self._touch()

    def validar(self) -> None:
        if self.context:
            issues = self.context.validator.validar()
            self.context.validator.issues = tuple(issues)
            erros = sum(i.severity == "ERROR" for i in issues)
            avisos = sum(i.severity == "WARN" for i in issues)
            self.status = f"Validação: {erros} erros | {avisos} avisos"

    def toggle_debug(self) -> None:
        self.status = "Debug semântico disponível via F3"

    def _touch(self):
        self.dirty = True
        if self.context:
            self.context.reindexar()

    @staticmethod
    def _region_json(item: Region):
        return {
            "id": item.id,
            "nome": item.nome,
            "tipo": item.tipo,
            "x": item.x,
            "y": item.y,
            "colunas": item.colunas,
            "linhas": item.linhas,
            "papel": item.papel,
            "tier": item.tier,
            "risco": item.risco,
            "recompensa": item.recompensa,
            "entrada": item.entrada,
            "saida": item.saida,
            "tags": list(item.tags),
        }

    def _tile_do_objeto(self, obj):
        if isinstance(obj, Region):
            return (obj.x, obj.y)
        return (0, 0)

    def _preencher_contexto_selecao(self, tile):
        if not self.context:
            return
        c, lin = tile
        self.selecao.update(
            {
                "regiao": getattr(
                    self.context.region_service.no_tile(c, lin), "id", None
                ),
            }
        )

    @staticmethod
    def _proximo(valores, atual):
        valores = tuple(valores)
        try:
            return valores[(valores.index(atual) + 1) % len(valores)]
        except ValueError:
            return valores[0]
