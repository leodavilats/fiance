from __future__ import annotations

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[2]

_IGNORAR_DIR = {"historico", "node_modules", ".git", "build", "__pycache__"}

_CAMINHO = re.compile(r"(?<![\w/.-])((?:backend|mobile|docs)/[\w./-]*\.\w+)")

_SIMBOLO = re.compile(r"`?([\w./-]+\.py):(\d+)`?")

# Bloco de código é comando, não referência: `cd mobile && python tool/build_icons.py` está certo
# como comando e erraria como caminho de repositório.
_BLOCO = re.compile(r"```.*?```", re.DOTALL)


def _prosa(texto: str) -> str:
    return _BLOCO.sub("", texto)


def _documentos() -> list[pathlib.Path]:
    achados = [RAIZ / "CLAUDE.md", RAIZ / "README.md"]
    for caminho in (RAIZ / "docs").rglob("*.md"):
        if _IGNORAR_DIR & set(caminho.relative_to(RAIZ).parts):
            continue
        achados.append(caminho)
    return [c for c in achados if c.exists()]


DOCUMENTOS = _documentos()


def test_existem_documentos_para_conferir():
    assert len(DOCUMENTOS) >= 10, (
        f"só {len(DOCUMENTOS)} documentos encontrados. Se a documentação mudou de lugar, este "
        "verificador passa a não conferir nada — em silêncio, que é o defeito que ele existe "
        "para evitar."
    )


@pytest.mark.parametrize("documento", DOCUMENTOS, ids=lambda p: p.name)
def test_todo_arquivo_citado_existe(documento: pathlib.Path):
    texto = _prosa(documento.read_text(encoding="utf-8"))
    fantasmas = sorted(
        {
            citado
            for citado in _CAMINHO.findall(texto)
            if not (RAIZ / citado).exists() and not citado.endswith(".md")
        }
    )

    assert fantasmas == [], (
        f"{documento.relative_to(RAIZ)} cita arquivo que não existe: {fantasmas}. "
        "Documentação que descreve código inexistente instrui quem a lê — pessoa ou IA — a "
        "trabalhar num lugar que não existe. Foi o que aconteceu com `optimizer/`."
    )


@pytest.mark.parametrize("documento", DOCUMENTOS, ids=lambda p: p.name)
def test_toda_linha_citada_existe(documento: pathlib.Path):
    texto = _prosa(documento.read_text(encoding="utf-8"))
    curtos = []

    for arquivo, linha in _SIMBOLO.findall(texto):
        alvo = RAIZ / arquivo
        if not alvo.exists():
            continue
        total = len(alvo.read_text(encoding="utf-8").splitlines())
        if int(linha) > total:
            curtos.append(f"{arquivo}:{linha} (o arquivo tem {total} linhas)")

    assert curtos == [], (
        f"{documento.relative_to(RAIZ)} aponta para linha que não existe: {curtos}. "
        "Citação de linha envelhece a cada edição do arquivo; se apontar para fora, cite só o "
        "arquivo."
    )
