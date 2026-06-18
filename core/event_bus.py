# core/event_bus.py

import re
import threading
from collections import defaultdict
from typing import Any, Callable, dict, list


def _camel_to_snake(name: str) -> str:
    # Converte CamelCase para snake_case, removendo o
    # sufixo 'Event' ou 'Evento' se presente.
    if name.endswith("Event"):
        name = name[:-5]
    elif name.endswith("Evento"):
        name = name[:-6]
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class Event:
    # Classe base para todos os eventos do sistema.

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"


# Alias em português para conformidade com as diretrizes
Evento = Event


class Subscriber:
    """Classe base para assinantes de eventos (opcional)."""

    def handle_event(self, event: Event):
        """Método para tratar os eventos recebidos."""
        raise NotImplementedError("Subclasses devem implementar handle_event")


# Alias em português para conformidade com as diretrizes
Ouvinte = Subscriber


class EventBus:
    # Um barramento de eventos interno, thread-safe, para comunicação
    # desacoplada entre módulos.

    def __init__(self):
        self._subscribers: dict[Any, list[Callable[[Any], None]]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type: Any, handler: Callable[[Any], None]):
        # Inscreve um manipulador para um tipo de evento
        # (pode ser a classe do evento ou uma string).
        with self._lock:
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: Any, handler: Callable[[Any], None]):
        """Remove a inscrição de um manipulador para um tipo de evento."""
        with self._lock:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)

    def publish(self, event: Any, **kwargs):
        """Publica um evento para todos os ouvintes inscritos.
        Aceita tanto uma instância de evento quanto uma string
        identificadora (ex: 'voz_detectada').
        Se uma string for fornecida, os kwargs serão passados para construir
        a classe de evento correspondente.
        """
        if isinstance(event, str):
            event_lower = event.lower()
            classe_evento = _MAPA_EVENTOS.get(event_lower)
            if classe_evento:
                event_obj = classe_evento(**kwargs)
            else:
                event_obj = Event(**kwargs)
                event_obj._event_name = event
        else:
            event_obj = event

        tipo_evento = type(event_obj)

        # Determina todas as chaves possíveis de inscrição para este evento
        chaves = [tipo_evento, tipo_evento.__name__]

        nome_snake = _camel_to_snake(tipo_evento.__name__)
        chaves.append(nome_snake)

        if hasattr(event_obj, "_event_name"):
            chaves.append(event_obj._event_name)
            chaves.append(event_obj._event_name.lower())

        # Coleta os manipuladores exclusivos para evitar chamadas duplicadas
        handlers_to_call = []
        with self._lock:
            for chave in chaves:
                for handler in self._subscribers[chave]:
                    if handler not in handlers_to_call:
                        handlers_to_call.append(handler)

        # Executa os manipuladores fora do lock para evitar deadlocks
        # se um handler interagir com o EventBus
        for handler in handlers_to_call:
            try:
                handler(event_obj)
            except Exception as e:
                print(
                    f"[EventBus] Erro ao processar evento {tipo_evento.__name__}: {e}"
                )

    # Métodos em português (conforme GEMINI.md)
    def assinar(self, tipo_evento: Any, manipulador: Callable[[Any], None]):
        """Alias em português para subscribe."""
        self.subscribe(tipo_evento, manipulador)

    def desassinar(self, tipo_evento: Any, manipulador: Callable[[Any], None]):
        """Alias em português para unsubscribe."""
        self.unsubscribe(tipo_evento, manipulador)

    def publicar(self, evento: Any, **kwargs):
        """Alias em português para publish."""
        self.publish(evento, **kwargs)

    def limpar(self):
        """Remove todas as inscrições do barramento (útil para resets e testes)."""
        with self._lock:
            self._subscribers.clear()


# --- Definições de Eventos Específicos do Sistema ---


class VozDetectadaEvent(Event):
    """Disparado quando a voz do usuário é detectada e convertida em texto."""

    def __init__(self, texto: str):
        super().__init__(texto=texto)


class MusicaIniciadaEvent(Event):
    """Disparado quando uma música ou playlist é iniciada."""

    def __init__(self, musica_info: Any):
        super().__init__(musica_info=musica_info)


class MusicaPausadaEvent(Event):
    """Disparado quando a reprodução da música é pausada."""

    def __init__(self):
        super().__init__()


class PensamentoExibidoEvent(Event):
    """Disparado quando um pensamento do Sapo é exibido na tela."""

    def __init__(self, pensamento_texto: str):
        super().__init__(pensamento_texto=pensamento_texto)


class ClimaAtualizadoEvent(Event):
    """Disparado quando as informações de clima/tempo são atualizadas."""

    def __init__(self, clima_data: Any):
        super().__init__(clima_data=clima_data)


# Aliases em português para as classes de eventos
VozDetectadaEvento = VozDetectadaEvent
MusicaIniciadaEvento = MusicaIniciadaEvent
MusicaPausadaEvento = MusicaPausadaEvent
PensamentoExibidoEvento = PensamentoExibidoEvent
ClimaAtualizadoEvento = ClimaAtualizadoEvent

# Mapa para resolução dinâmica a partir de strings
_MAPA_EVENTOS = {
    "voz_detectada": VozDetectadaEvent,
    "musica_iniciada": MusicaIniciadaEvent,
    "musica_pausada": MusicaPausadaEvent,
    "pensamento_exibido": PensamentoExibidoEvent,
    "clima_atualizado": ClimaAtualizadoEvent,
    "vozdetectadaevent": VozDetectadaEvent,
    "musicainiciadaevent": MusicaIniciadaEvent,
    "musicapausadaevent": MusicaPausadaEvent,
    "pensamentoexibidoevent": PensamentoExibidoEvent,
    "climaatualizadoevent": ClimaAtualizadoEvent,
    "vozdetectadaevento": VozDetectadaEvent,
    "musicainiciadaevento": MusicaIniciadaEvent,
    "musicapausadaevento": MusicaPausadaEvent,
    "pensamentoexibidoevento": PensamentoExibidoEvent,
    "climaatualizadoevento": ClimaAtualizadoEvent,
}

# Instância global do EventBus para uso compartilhado em todo o projeto
event_bus = EventBus()
