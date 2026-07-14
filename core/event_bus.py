# core/event_bus.py

import re
import threading
from collections import defaultdict
from typing import Any, Callable, Dict, List


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
        self._subscribers: Dict[Any, List[Callable[[Any], None]]] = defaultdict(list)
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

    def publish(self, event: Any, *args, **kwargs):
        if isinstance(event, str):
            event_lower = event.lower()
            classe_evento = _MAPA_EVENTOS.get(event_lower)

            if classe_evento:
                event_obj = classe_evento(*args, **kwargs)
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

    def publicar(self, evento: Any, *args, **kwargs):
        self.publish(evento, *args, **kwargs)

    def limpar(self):
        """Remove todas as inscrições do barramento (útil para resets e testes)."""
        with self._lock:
            self._subscribers.clear()


# --- Definições de Eventos Específicos do Sistema ---


class ClimaAtualizadoEvent(Event):
    """Disparado quando as informações de clima/tempo são atualizadas."""

    def __init__(self, clima_data: Any):
        super().__init__(clima_data=clima_data)


class TTSIniciadoEvent(Event):
    pass


class TTSFinalizadoEvent(Event):
    pass


class VooIniciadoEvent(Event):
    pass


class DescendoParaDormirEvent(Event):
    pass


class PensamentoSapoEvent(Event):
    def __init__(self, texto: str, duracao: float = 6):
        super().__init__(texto=texto, duracao=duracao)


# Aliases em português para as classes de eventos
ClimaAtualizadoEvento = ClimaAtualizadoEvent

# Mapa para resolução dinâmica a partir de strings
_MAPA_EVENTOS = {
    "clima_atualizado": ClimaAtualizadoEvent,
    "tts_iniciado": TTSIniciadoEvent,
    "tts_finalizado": TTSFinalizadoEvent,
    "voo_iniciado": VooIniciadoEvent,
    "descendo_para_dormir": DescendoParaDormirEvent,
    "pensamento_sapo": PensamentoSapoEvent,
}

# Instância global do EventBus para uso compartilhado em todo o projeto
event_bus = EventBus()
