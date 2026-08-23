from html import escape

from tests.integration.visual.gif import gerar_gif

VISUAIS = [
    "personagem_perto_inimigo",
    "personagem_com_construcao_inimiga",
    "inimigos_em_niveis_diferentes",
    "movimento_com_obstaculo",
    "movimento_degrau",
    "aldeao_corta_1_arvore",
    "aldeoes_cortam_2_arvore",
    "aldeoes_cortam_3_arvore",
    "soldado_ataca_goblin",
    "soldado_contorna_construcao",
    "soldado_defende_construcao",
    "dois_soldados_atacam_construcao",
    "goblin_no_degrau",
]


def gerar_relatorio(resultados, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    # Limpa os resultados anteriores para que somente os GIFs e o relatório atual permaneçam.
    for p in pasta.iterdir():
        if p.is_file():
            p.unlink()

    by_name = {r.nome: r for r in resultados}
    cards = []
    for nome in VISUAIS:
        gif_arquivo = pasta / f"{nome}.gif"
        result = by_name.get(nome)
        try:
            gif_meta = {}
            if result and result.trace:
                gif_arquivo, gif_meta = gerar_gif(
                    nome, result, pasta, fps=14, max_frames=36
                )
            imagem = (
                f"<div class='media'><a href='{gif_arquivo.name}'><img src='{gif_arquivo.name}' alt='{escape(nome)} · GIF'></a>"
                f"<small>GIF real do jogo · {gif_meta.get('gif_frames', 0)} frames · 14 FPS · sprites/terreno reais · clique para abrir</small></div>"
            )
        except Exception as exc:
            imagem = f"<div class='no-image'>Visualização indisponível: {escape(str(exc))}</div>"
        status = (
            "PASSOU"
            if result and result.ok
            else "FALHOU"
            if result
            else "NÃO EXECUTADO"
        )
        classe = "ok" if result and result.ok else "fail" if result else "skip"
        erro = (
            f"<details><summary>erro</summary><pre>{escape(result.erro)}</pre></details>"
            if result and result.erro
            else ""
        )
        cards.append(f"""
        <article class='{classe}'>
          <div class='head'><h2>{escape(nome)}</h2><span>{status}</span></div>
          <p>{(result.duracao if result else 0):.2f}s · GIF do fluxo real</p>
          {imagem}
          {erro}
        </article>
        """)

    total = len(resultados)
    ok = sum(r.ok for r in resultados)
    fail = total - ok
    html = f"""<!doctype html>
<html lang='pt-BR'>
<head>
<meta charset='utf-8'>
<title>Sapo Sapudo - Laboratório Integrado</title>
<style>
body{{font:15px Arial,sans-serif;background:#102735;color:#eef6f8;margin:24px;}}
h1{{margin:0 0 8px;font-size:28px}} .summary{{margin-bottom:18px;color:#cfe6ef}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:16px;}}
 .no-image{{padding:24px;background:#102735;border-radius:8px;color:#ffd8d8}} article{{background:#183f4c;border-radius:12px;padding:14px;box-shadow:0 4px 20px rgba(0,0,0,.18);overflow:hidden}}
article.ok{{border-left:6px solid #76d98b}} article.fail{{border-left:6px solid #e56b62}} article.skip{{border-left:6px solid #d6bb62}}
.head{{display:flex;justify-content:space-between;gap:12px;align-items:center}} h2{{font-size:18px;margin:0;word-break:break-word}} .head span{{font-weight:700}}
p{{margin:7px 0 12px;color:#bdd5dc}} img{{display:block;width:100%;height:auto;background:#102735;border-radius:8px;image-rendering:pixelated}} .media small{{display:block;margin-top:6px;color:#9fb9c2}} .media a{{text-decoration:none}}
details{{margin-top:10px}} pre{{white-space:pre-wrap;color:#ffd8d8}}
.legend{{margin:10px 0 16px;padding:10px 12px;background:#173642;border-radius:8px;color:#cfe6ef}}
</style>
</head>
<body>
<h1>🧪 Sapo Sapudo · Laboratório Integrado</h1>
<div class='summary'><strong>{ok} OK</strong> · <strong>{fail} FALHARAM</strong> · <strong>{total} TOTAL</strong></div>
<div class='legend'>Cada cenário possui um GIF independente renderizado com os assets reais do jogo e as posições/estados capturados pelo runtime do teste. O enquadramento é aproximado da câmera do jogo, com amostragem e aceleração para manter o fluxo legível.</div>
<div class='grid'>{"".join(cards)}</div>
</body>
</html>"""
    destino = pasta / "index.html"
    destino.write_text(html, encoding="utf-8")
    return destino
