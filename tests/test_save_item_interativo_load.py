from core.save_game import SaveGameManager
from domains.interacao_item import ItemInterativo


def test_resolver_item_interativo_retorna_instancia_real(monkeypatch):
    class Cenario:
        pass

    mgr = object.__new__(SaveGameManager)
    mgr.cenario = Cenario()
    estado = {
        "__object_state__": {
            "nome": "machado",
            "x": 12,
            "y": 34,
            "descricao": "Machado de Bernardo",
            "raio": 46,
            "coletado": True,
            "tipo_sprite": "machado",
        },
        "__object_type__": "ItemInterativo",
    }
    item = mgr._resolver_valor(estado, {})
    assert isinstance(item, ItemInterativo)
    assert item.nome == "machado"
    assert item.coletado is True
    assert item.x == 12 and item.y == 34
