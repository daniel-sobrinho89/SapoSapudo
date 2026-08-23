from pathlib import Path

from tests.integration.visual.real_scene import gerar_gif_real


def gerar_gif(nome, resultado, pasta, fps=14, max_frames=36):
    destino = Path(pasta) / f"{nome}.gif"
    return gerar_gif_real(
        nome,
        resultado,
        destino,
        fps=fps,
        max_frames=max_frames,
        size=(760, 460),
    )
