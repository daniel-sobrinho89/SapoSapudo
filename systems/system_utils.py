"""Helpers para orquestração comum de systems (evita duplicação leve).

Funções pequenas que chamam métodos presentes em animacoes/respiracao/animacao_folha
e suportam diferenças mínimas entre personagens (usa hasattr quando necessário).
"""

def atualizar_sistemas_basicos(
    animacoes,
    respiracao,
    animacao_folha,
    dt,
    ambiente,
    entity=None,
    clima_service=None,
    frasco_rect=None
):
    # animações (padrão)
    animacoes.atualizar(dt)

    # transições opcionais (caso o objeto de animacoes implemente)
    if hasattr(animacoes, "atualizar_transicoes") and entity is not None and clima_service is not None and frasco_rect is not None:
        try:
            animacoes.atualizar_transicoes(
                dt,
                entity,
                clima_service.clima_disponivel,
                frasco_rect
            )
        except Exception:
            # não forçar assinatura exata — ignorar se falhar
            pass

    # respiração
    respiracao.atualizar(dt, getattr(animacoes, "dormindo", False))

    # animacao de folha (micro-movimento)
    animacao_folha.atualizar(
        dt,
        respiracao.intensidade,
        ambiente
    )
