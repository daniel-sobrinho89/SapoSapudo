import json

import utils.kivy_adapter as kivy_adapter
from utils.paths import BASE_DIR


class SpriteAnimadoRenderer:
    LARGURA_BARRA_VIDA = 90
    ALTURA_BARRA_VIDA = 16
    OFFSET_Y_BARRA_VIDA = 50

    with open(BASE_DIR / "data/sprites_config.json", encoding="utf8") as f:
        CONFIG = json.load(f)

    def __init__(
        self,
        tela,
        assets,
        transform,
        tipo,
        escala,
    ):
        self.tela = tela
        self.assets = assets
        self.transform = transform

        self.tipo = tipo.lower()

        self.escala = escala
        self.escala_x = escala
        self.escala_y = escala

        self.carregado = False
        self._indice = 0

        self.frames = {}
        self._partes_barra_vida = None
        self._bbox_frames = {}
        self.ciclo_dia_noite = None
        self._cache_iluminacao = {}

        config = self.CONFIG[self.tipo]

        self.flip = config["flip"]
        self._fila = list(config["animacoes"].items())

        for grupo, _ in self._fila:
            self.frames[grupo] = []

            if self.flip:
                self.frames[f"{grupo}_flip"] = []

    # =====================================
    # LOAD
    # =====================================

    def atualizar_carregamento(
        self,
        quantidade_por_frame=3,
    ):
        if self.carregado:
            return

        for _ in range(quantidade_por_frame):
            if self._indice >= len(self._fila):
                self._finalizar_carregamento()
                return

            grupo, dados = self._fila[self._indice]

            self._indice += 1

            spritesheet = self.assets.carregar(dados["arquivo"])

            frames = self.transform.recortar_spritesheet(
                spritesheet,
                linhas=1,
                colunas=dados["frames"],
            )

            self.frames[grupo] = frames
            self._bbox_frames[grupo] = [frame.get_bounding_rect() for frame in frames]

            if self.flip:
                frames_flip = [self.transform.espelhar(frame) for frame in frames]
                self.frames[f"{grupo}_flip"] = frames_flip
                self._bbox_frames[f"{grupo}_flip"] = [
                    frame.get_bounding_rect() for frame in frames_flip
                ]

    def _finalizar_carregamento(self):
        self.calcular_layout()
        self.carregado = True

    # =====================================
    # LAYOUT
    # =====================================

    def obter_tamanho(self, frame, escala=1.0, escala_x=1.0, escala_y=1.0):
        return (
            max(1, int(frame.get_width() * self.escala * escala * escala_x)),
            max(1, int(frame.get_height() * self.escala * escala * escala_y)),
        )

    def calcular_layout(self):
        self.grupo_padrao = self._fila[0][0]
        frame = self.frames[self.grupo_padrao][0]
        self.largura, self.altura = self.obter_tamanho(frame)

    # =====================================
    # FRAME
    # =====================================

    def obter_frame_animacao(self, animacoes):
        if not self.carregado:
            return None

        seletor, indice = animacoes.obter_selecao_frame()

        frames = self.frames.get(
            seletor,
            self.frames[self.grupo_padrao],
        )

        indice = min(indice, len(frames) - 1)

        return frames[indice]

    # =====================================
    # RENDER
    # =====================================

    def renderizar(
        self,
        entidade,
        animacoes,
        camera,
        alpha=255,
        escala=1.0,
        cor=None,
    ):
        if not self.carregado:
            return
        if getattr(entidade, "visivel", True) is False:
            return

        frame = self.obter_frame_animacao(animacoes)

        if frame is None:
            return

        seletor, indice_frame = animacoes.obter_selecao_frame()

        escala_entidade_x = getattr(entidade, "escala_x", 0.9)
        escala_entidade_y = getattr(entidade, "escala_y", 0.9)

        largura, altura = self.obter_tamanho(
            frame,
            escala,
            escala_entidade_x,
            escala_entidade_y,
        )

        largura_mundo = largura
        altura_mundo = altura

        if not camera.visivel(
            entidade.x,
            entidade.y,
            largura,
            altura,
        ):
            return

        # A iluminação é calculada sobre o frame-fonte, que permanece estável
        # entre os frames de renderização. O cache antigo usava id() do frame
        # já escalado, portanto criava uma textura nova a cada frame.
        fator_luz = None
        if self.ciclo_dia_noite is not None:
            fator_luz = self.ciclo_dia_noite.nivel_luz

        cor_chave = tuple(cor) if cor is not None else None
        cache_key = (
            id(frame),
            int(largura * camera.zoom),
            int(altura * camera.zoom),
            round(fator_luz, 3) if fator_luz is not None else None,
            cor_chave,
        )
        cache_entry = self._cache_iluminacao.get(cache_key)
        frame_render = None
        if cache_entry is not None:
            fonte_cacheada, frame_render = cache_entry
            if fonte_cacheada is not frame:
                frame_render = None

        if frame_render is None:
            frame_base = frame
            if cor is not None or fator_luz is not None:
                frame_base = frame.copy()

                if cor is not None:
                    frame_base.multiplicar_cor(cor)

                if fator_luz is not None and abs(fator_luz - 1.0) >= 1e-6:
                    frame_base.ajustar_luminosidade(fator_luz)

            frame_render = self.transform.escalar(
                frame_base,
                (
                    int(largura * camera.zoom),
                    int(altura * camera.zoom),
                ),
            )
            # Mantém referência forte ao frame-fonte. Além de validar identidade,
            # isso impede colisões por reutilização de id() do objeto.
            self._cache_iluminacao[cache_key] = (frame, frame_render)

            # Evita crescimento ilimitado caso o zoom mude continuamente.
            if len(self._cache_iluminacao) > 512:
                for chave in list(self._cache_iluminacao)[:128]:
                    del self._cache_iluminacao[chave]

        frame = frame_render
        if alpha != 255:
            # Nunca alterar a textura armazenada no cache. Um alpha diferente
            # para um personagem/efeito não pode contaminar os próximos usos.
            frame = frame.copy()
            frame.set_alpha(alpha)

        bboxes = self._bbox_frames.get(seletor)
        if bboxes:
            bbox = bboxes[min(indice_frame, len(bboxes) - 1)]
        else:
            bbox = frame.get_bounding_rect()

        x, y = camera.tela(
            entidade.x,
            entidade.y,
        )

        rect = frame.get_rect(center=(int(x), int(y)))
        entidade.render_rect = rect
        self.tela.blit(
            frame,
            rect,
        )

        fator_bbox_x = self.escala * escala * escala_entidade_x
        fator_bbox_y = self.escala * escala * escala_entidade_y
        bbox_x = bbox.x * fator_bbox_x
        bbox_y = bbox.y * fator_bbox_y
        bbox_w = bbox.w * fator_bbox_x
        bbox_h = bbox.h * fator_bbox_y

        entidade.corpo_rect = kivy_adapter.Rect(
            entidade.x - largura_mundo / 2 + bbox_x,
            entidade.y - altura_mundo / 2 + bbox_y,
            max(1, bbox_w),
            max(1, bbox_h),
        )

        entidade.base_pe_y = entidade.corpo_rect.bottom

    def renderizar_barra_vida(
        self,
        personagem,
        camera,
        proporcao_vida,
        renderer_preenchimento,
    ):
        """Renderiza a barra usando as três peças reais do asset."""
        if not self.carregado or not renderer_preenchimento.carregado:
            return

        base = self.frames["ocioso"][0]
        preenchimento = renderer_preenchimento.frames["ocioso"][0]
        proporcao = max(0.0, min(1.0, float(proporcao_vida)))

        largura_barra = self.LARGURA_BARRA_VIDA
        altura_barra = self.ALTURA_BARRA_VIDA

        cache_key = (id(base), largura_barra, altura_barra)
        barra_base = getattr(self, "_barra_vida_base_cache", None)
        if (
            barra_base is None
            or getattr(self, "_barra_vida_base_cache_key", None) != cache_key
        ):
            partes = self._obter_partes_barra_vida(base)
            recortadas = []
            for parte in partes:
                bbox = parte.get_bounding_rect()
                if bbox.w > 0 and bbox.h > 0:
                    recortadas.append(
                        parte.subsurface((bbox.x, bbox.y, bbox.w, bbox.h))
                    )
                else:
                    recortadas.append(parte)

            largura_visivel = sum(p.get_width() for p in recortadas)
            altura_visivel = max(p.get_height() for p in recortadas)
            composto = kivy_adapter.Surface(
                (largura_visivel, altura_visivel),
                kivy_adapter.SRCALPHA,
            )
            cursor_x = 0
            for parte in recortadas:
                y = (altura_visivel - parte.get_height()) // 2
                composto.blit(parte, (cursor_x, y))
                cursor_x += parte.get_width()

            barra_base = self.transform.escalar(
                composto,
                (largura_barra, altura_barra),
            )
            self._barra_vida_base_cache = barra_base
            self._barra_vida_base_cache_key = cache_key

        barra = kivy_adapter.Surface(
            (largura_barra, altura_barra),
            kivy_adapter.SRCALPHA,
        )

        fill_bbox = preenchimento.get_bounding_rect()
        faixa = None
        margem_x = 5
        y_fill = 0
        if fill_bbox.w > 0 and fill_bbox.h > 0 and proporcao > 0.0:
            largura_interna = max(1, largura_barra - margem_x * 2)
            largura_preenchimento = int(round(largura_interna * proporcao))
            faixa = preenchimento.subsurface(
                (fill_bbox.x, fill_bbox.y, fill_bbox.w, fill_bbox.h)
            )
            faixa = self.transform.escalar(
                faixa,
                (largura_preenchimento, max(2, min(4, faixa.get_height()))),
            )
            y_fill = (altura_barra - faixa.get_height()) // 2

        # A moldura deve ficar atrás do preenchimento.
        # A ordem anterior desenhava a base por último e cobria a vida.
        barra.blit(barra_base, (0, 0))
        if faixa is not None:
            barra.blit(faixa, (margem_x, y_fill))
        x, y = camera.tela(
            personagem.x,
            personagem.y + self.OFFSET_Y_BARRA_VIDA,
        )
        self.tela.blit(barra, barra.get_rect(center=(int(x), int(y))))

    def _obter_partes_barra_vida(self, base=None):
        if getattr(self, "_partes_barra_vida", None) is not None:
            return self._partes_barra_vida

        base = base or self.frames["ocioso"][0]
        largura_componente = base.get_width() // 5
        altura = base.get_height()

        self._partes_barra_vida = (
            base.subsurface((0, 0, largura_componente, altura)),
            base.subsurface((largura_componente * 2, 0, largura_componente, altura)),
            base.subsurface((largura_componente * 4, 0, largura_componente, altura)),
        )

        return self._partes_barra_vida
