from pathlib import Path

# BASE_DIR aponta para a raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent


def asset_path(*parts):
    return BASE_DIR.joinpath(*parts)
