"""Captura as telas do aplicativo como PNG, para revisão visual por pessoa ou por IA.

Uso:
    python tool/capturar_telas.py           # baixa as fontes se faltarem e captura
    python tool/capturar_telas.py --limpar  # apaga as capturas antigas antes

Roda em `flutter test`, sem emulador e sem backend: a rede é dublada e os dados são de exemplo.
As fontes precisam ser baixadas uma vez porque o aplicativo as busca em runtime pelo google_fonts —
sem elas, o Flutter desenha caixas no lugar do texto, e a imagem engana quem for avaliá-la.

Complementa `tool/catalogo_de_telas.py`, que extrai o texto e a estrutura sem renderizar.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MOBILE = RAIZ / "mobile"
FONTES = MOBILE / "build" / "fontes"
TELAS = MOBILE / "build" / "catalogo" / "telas"

# Variáveis de peso, do repositório oficial do Google Fonts. Licença OFL.
_FONTES = {
    "IBMPlexSans-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/ibmplexsans/IBMPlexSans%5Bwdth%2Cwght%5D.ttf"
    ),
    "SourceSerif4-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/sourceserif4/"
        "SourceSerif4%5Bopsz%2Cwght%5D.ttf"
    ),
}


def _copiar_icones() -> None:
    destino = FONTES / "MaterialIcons-Regular.otf"
    if destino.exists():
        return

    flutter = shutil.which("flutter")
    if not flutter:
        print("  flutter nao encontrado no PATH; os icones sairao como quadrados vazios")
        return

    raiz = pathlib.Path(flutter).resolve().parent.parent
    for candidato in raiz.rglob("materialicons-regular.otf"):
        shutil.copy(candidato, destino)
        return
    for candidato in raiz.rglob("MaterialIcons-Regular.otf"):
        shutil.copy(candidato, destino)
        return

    print("  fonte de icones do Flutter nao localizada; eles sairao como quadrados vazios")


def _baixar_fontes() -> bool:
    FONTES.mkdir(parents=True, exist_ok=True)
    _copiar_icones()

    for nome, url in _FONTES.items():
        destino = FONTES / nome
        if destino.exists() and destino.stat().st_size > 10_000:
            continue

        print(f"baixando {nome}...")
        try:
            pedido = urllib.request.Request(url, headers={"User-Agent": "fiance-captura"})
            with urllib.request.urlopen(pedido, timeout=60) as resposta:
                destino.write_bytes(resposta.read())
        except Exception as erro:
            print(f"  nao foi possivel baixar {nome}: {erro}")
            print(
                "  Sem a fonte, a captura sai com caixas no lugar do texto. Baixe manualmente de "
                f"{url} e salve em {destino}."
            )
            return False

    return True


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limpar", action="store_true", help="apaga as capturas antigas")
    args = parser.parse_args()

    if not _baixar_fontes():
        return 1

    if args.limpar and TELAS.exists():
        shutil.rmtree(TELAS)

    print("capturando...")
    subprocess.run(
        ["flutter", "test", "captura/telas_test.dart"],
        cwd=MOBILE,
        shell=True,
        capture_output=True,
    )

    imagens = sorted(TELAS.glob("*.png")) if TELAS.exists() else []
    if not imagens:
        print(
            "nenhuma imagem foi escrita. Rode "
            "`flutter test captura/telas_test.dart` em mobile/ "
            "para ver o erro."
        )
        return 1

    total = sum(i.stat().st_size for i in imagens)
    print(f"\n{len(imagens)} imagens, {total / 1024 / 1024:.1f} MB -> {TELAS.relative_to(RAIZ)}")
    for imagem in imagens:
        print(f"  {imagem.name}")

    print(
        "\nPara avaliacao, envie as imagens junto com "
        "build/catalogo/COMO-AVALIAR.md (gerado por tool/catalogo_de_telas.py)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
