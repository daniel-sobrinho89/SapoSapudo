from core.animacoes import Animacoes


def test_orientacao_por_deslocamento_das_unidades_afetadas():
    # O spritesheet de cada unidade possui uma orientação-base própria.
    # Estes testes garantem que "olhar para o alvo" não dependa de uma regra
    # global de flip.
    casos = {
        "aldeao": {"esquerda": True, "direita": False},
        "bandido": {"esquerda": True, "direita": False},
        "ovelha": {"esquerda": True, "direita": False},
        "urso": {"esquerda": True, "direita": False},
        "sapudo": {"esquerda": True, "direita": False},
    }
    for tipo, esperado in casos.items():
        animacoes = Animacoes(tipo)
        assert animacoes.flip_para_direcao(-100) is esperado["esquerda"]
        assert animacoes.flip_para_direcao(100) is esperado["direita"]
