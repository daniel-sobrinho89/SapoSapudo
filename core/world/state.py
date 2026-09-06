from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class FaseDia(StrEnum):
    MANHA = "manha"
    TARDE = "tarde"
    NOITE = "noite"


class Clima(StrEnum):
    NORMAL = "normal"
    CHUVA = "chuva"
    SECA = "seca"


class EstadoRecurso(StrEnum):
    DISPONIVEL = "disponivel"
    COLETADO = "coletado"
    REGENERANDO = "regenerando"


class EstadoFauna(StrEnum):
    PASTANDO = "pastando"
    FUGINDO = "fugindo"
    DORMINDO = "dormindo"
    MIGRANDO = "migrando"


class EstadoAmeaca(StrEnum):
    CALMA = "calma"
    ALERTA = "alerta"
    OCUPADA = "ocupada"


@dataclass(frozen=True)
class WorldEvent:
    id: str
    tipo: str
    duracao: float
    restante: float
    regiao: str | None = None

    @property
    def ativo(self) -> bool:
        return self.restante > 0


@dataclass
class WorldState:
    """Estado runtime mutável que dá consequências temporais ao world model."""

    tempo_simulado: float = 0.0
    duracao_dia: float = 180.0
    fase: FaseDia = FaseDia.MANHA
    clima: Clima = Clima.NORMAL
    eventos_habilitados: bool = False
    recursos: dict[str, EstadoRecurso] = field(default_factory=dict)
    temporizadores_recursos: dict[str, float] = field(default_factory=dict)
    fauna: dict[str, EstadoFauna] = field(default_factory=dict)
    ameacas: dict[str, EstadoAmeaca] = field(default_factory=dict)
    eventos: dict[str, WorldEvent] = field(default_factory=dict)
    _recursos_regenerados: list[str] = field(
        default_factory=list, init=False, repr=False
    )
    duracao_respawn: float = 45.0
    intervalo_clima: float = 75.0
    _tempo_clima: float = 0.0

    def registrar_recurso(self, entidade_id: str) -> None:
        self.recursos.setdefault(entidade_id, EstadoRecurso.DISPONIVEL)

    def marcar_recurso_coletado(self, entidade_id: str) -> None:
        self.recursos[entidade_id] = EstadoRecurso.COLETADO
        self.temporizadores_recursos[entidade_id] = self.duracao_respawn

    def recurso_disponivel(self, entidade_id: str) -> bool:
        return (
            self.recursos.get(entidade_id, EstadoRecurso.DISPONIVEL)
            == EstadoRecurso.DISPONIVEL
        )

    def registrar_fauna(self, entidade_id: str) -> None:
        self.fauna.setdefault(entidade_id, self.estado_fauna_atual())

    def registrar_ameaca(self, regiao_id: str) -> None:
        self.ameacas.setdefault(regiao_id, EstadoAmeaca.CALMA)

    def estado_fauna_atual(self) -> EstadoFauna:
        if self.fase == FaseDia.NOITE:
            return EstadoFauna.DORMINDO
        if self.clima == Clima.CHUVA:
            return EstadoFauna.PASTANDO
        return EstadoFauna.PASTANDO

    def marcar_ameaca_alerta(self, regiao_id: str) -> None:
        self.ameacas[regiao_id] = EstadoAmeaca.ALERTA

    def adicionar_evento(
        self, evento_id: str, tipo: str, duracao: float, regiao: str | None = None
    ) -> None:
        if not self.eventos_habilitados:
            return
        self.eventos[evento_id] = WorldEvent(evento_id, tipo, duracao, duracao, regiao)

    def _atualizar_clima(self, dt: float) -> None:
        self._tempo_clima += dt
        if self._tempo_clima < self.intervalo_clima:
            return
        self._tempo_clima = 0.0
        anterior = self.clima
        sequencia = (Clima.NORMAL, Clima.CHUVA, Clima.NORMAL, Clima.SECA)
        indice = sequencia.index(self.clima)
        self.clima = sequencia[(indice + 1) % len(sequencia)]
        if self.eventos_habilitados and self.clima != anterior:
            self.adicionar_evento(
                f"clima:{int(self.tempo_simulado)}",
                "mudanca_clima",
                duracao=min(30.0, self.intervalo_clima * 0.5),
            )

    def atualizar(self, dt: float) -> None:
        dt = max(0.0, float(dt))
        self._recursos_regenerados.clear()
        self.tempo_simulado += dt
        if self.duracao_dia <= 0:
            self.duracao_dia = 180.0
        fase = int((self.tempo_simulado % self.duracao_dia) / (self.duracao_dia / 3.0))
        self.fase = (FaseDia.MANHA, FaseDia.TARDE, FaseDia.NOITE)[min(fase, 2)]

        for evento_id, evento in list(self.eventos.items()):
            restante = evento.restante - dt
            if restante <= 0:
                self.eventos.pop(evento_id, None)
            else:
                self.eventos[evento_id] = WorldEvent(
                    evento.id, evento.tipo, evento.duracao, restante, evento.regiao
                )

        self._atualizar_clima(dt)

        for entidade_id, restante in list(self.temporizadores_recursos.items()):
            restante -= dt
            if restante <= 0:
                self.temporizadores_recursos.pop(entidade_id, None)
                self.recursos[entidade_id] = EstadoRecurso.DISPONIVEL
                self._recursos_regenerados.append(entidade_id)
            else:
                self.temporizadores_recursos[entidade_id] = restante
                self.recursos[entidade_id] = EstadoRecurso.REGENERANDO

        if self.fase == FaseDia.NOITE:
            estado = EstadoFauna.DORMINDO
        elif self.clima == Clima.CHUVA:
            estado = EstadoFauna.PASTANDO
        else:
            estado = EstadoFauna.PASTANDO
        for entidade_id in list(self.fauna):
            self.fauna[entidade_id] = estado

    def consumir_recursos_regenerados(self) -> tuple[str, ...]:
        resultado = tuple(self._recursos_regenerados)
        self._recursos_regenerados.clear()
        return resultado

    @property
    def atividade(self) -> float:
        base = 0.55 if self.fase == FaseDia.NOITE else 1.0
        if self.clima == Clima.CHUVA:
            base *= 0.85
        elif self.clima == Clima.SECA:
            base *= 0.90
        return base

    def snapshot(self) -> dict:
        return {
            "tempo_simulado": round(self.tempo_simulado, 3),
            "fase": self.fase.value,
            "clima": self.clima.value,
            "atividade": round(self.atividade, 3),
            "eventos_habilitados": self.eventos_habilitados,
            "temporizadores_recursos": {
                k: round(v, 3) for k, v in self.temporizadores_recursos.items()
            },
            "tempo_clima": round(self._tempo_clima, 3),
            "recursos": {k: v.value for k, v in self.recursos.items()},
            "fauna": {k: v.value for k, v in self.fauna.items()},
            "ameacas": {k: v.value for k, v in self.ameacas.items()},
            "eventos": {
                k: {
                    "tipo": e.tipo,
                    "restante": round(e.restante, 2),
                    "regiao": e.regiao,
                }
                for k, e in self.eventos.items()
            },
        }
