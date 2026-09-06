from core.game_config import obter_config
from render.asset_manager import asset_manager
from render.transform_utils import TransformUtils


class ObjetoInterativoRenderer:
    def __init__(self, tela):
        self.tela = tela
        self._transform = TransformUtils()
        self._cache = {}
        self.ciclo_dia_noite = None
        self._cache_iluminacao = {}

    def _obter_sprite(self, objeto):
        tipo = getattr(objeto, "tipo_sprite", objeto.nome).lower()
        cache = self._cache.get(tipo)
        if cache is not None:
            return cache

        config = obter_config(tipo)
        animacoes = config.get("animacoes", {})
        dados = animacoes.get("ocioso")
        if not dados:
            return None

        sprite = asset_manager.carregar(dados["arquivo"])
        frames = self._transform.recortar_spritesheet(
            sprite, linhas=1, colunas=dados.get("frames", 1)
        )
        if not frames:
            return None

        frame = frames[0]
        escala = float(config.get("renderer", {}).get("escala", 1.0))
        if escala != 1.0:
            frame = self._transform.escalar(
                frame,
                (
                    max(1, int(frame.get_width() * escala)),
                    max(1, int(frame.get_height() * escala)),
                ),
            )

        self._cache[tipo] = frame
        return frame

    def renderizar(self, objeto, camera):
        if objeto.coletado:
            return

        frame = self._obter_sprite(objeto)
        if frame is None:
            return

        if self.ciclo_dia_noite is not None:
            fator_luz = self.ciclo_dia_noite.nivel_luz
            cache_key = (id(frame), self.ciclo_dia_noite.chave_iluminacao)
            cache_entry = self._cache_iluminacao.get(cache_key)
            frame_lit = None
            if cache_entry is not None:
                fonte_cacheada, frame_lit = cache_entry
                if fonte_cacheada is not frame:
                    frame_lit = None
            if frame_lit is None:
                frame_lit = frame.copy()
                if abs(fator_luz - 1.0) >= 1e-6:
                    frame_lit.ajustar_luminosidade(fator_luz)
                self._cache_iluminacao[cache_key] = (frame, frame_lit)
            frame = frame_lit

        x, y = camera.tela(objeto.x, objeto.y)
        rect = frame.get_rect(center=(int(x), int(y)))
        self.tela.blit(frame, rect)
        objeto.render_rect = rect
