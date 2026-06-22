"""Helpers para orquestração comum de systems (evita duplicação leve).

Funções pequenas que chamam métodos presentes em animacoes/respiracao/animacao_folha
e suportam diferenças mínimas entre personagens (usa hasattr quando necessário).
"""

from contextlib import suppress


def atualizar_sistemas_basicos(
    animacoes,
    respiracao,
    dt,
    ambiente,
    animacao_folha=None,
    entity=None,
    clima_service=None,
    frasco_rect=None,
):
    # animações (padrão)
    animacoes.atualizar(dt)

    # transições opcionais (caso o objeto de animacoes implemente)
    if (
        hasattr(animacoes, "atualizar_transicoes")
        and entity is not None
        and clima_service is not None
        and frasco_rect is not None
    ):
        with suppress(Exception):
            animacoes.atualizar_transicoes(
                dt, entity, clima_service.clima_disponivel, frasco_rect
            )

    # respiração
    respiracao.atualizar(dt, getattr(animacoes, "dormindo", False))

    # animacao de folha (micro-movimento)
    if animacao_folha is not None:
        animacao_folha.atualizar(dt, respiracao.intensidade, ambiente)
