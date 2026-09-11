#!/usr/bin/env python3
"""Remove comentários do backend (Python) e do mobile (Dart).

Nem tudo que começa com `#` ou `//` é comentário. Estas linhas são **diretiva**, lidas por uma
máquina, e removê-las quebra a esteira:

* Python — `# noqa`, `# type:`, `# pragma:`, `# fmt:`, `# ruff:`, `# mypy:`, `# isort:`,
  `# nosec`, o shebang e a declaração de codificação;
* Dart — `// ignore:`, `// ignore_for_file:`, `// coverage:`;
* Dart, específico deste repositório — `// design-exception: regra — motivo`, que é contrato com
  `mobile/test/lint_ui_test.dart`: sem ele a regra escapada volta a reprovar.

Por padrão elas ficam. `--tudo` as remove junto, e aí a esteira precisa ser reparada à mão.

Docstring de Python **não é comentário** e por padrão não sai: três rotas do backend usam a sua
como descrição do OpenAPI, e `__doc__` é legível em tempo de execução. `--docstrings` as remove.

Uso:

    python tool/remover_comentarios.py                 # relatório, não escreve
    python tool/remover_comentarios.py --aplicar
    python tool/remover_comentarios.py --aplicar --docstrings
    python tool/remover_comentarios.py backend/app --aplicar

Depois de aplicar, rode a esteira: o Python precisa de `ruff format` para recompor as linhas em
branco entre definições, e o Dart **não** pode passar por `dart format` (o formatador reescreve
`design_tokens.dart` e quebra os `if` de uma linha que o repositório mantém).
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tokenize
from dataclasses import dataclass, field
from pathlib import Path

DIRETIVAS_PY = re.compile(
    r"^#\s*(noqa|type:|pragma:|fmt:|ruff:|mypy:|isort:|nosec|coding[:=]|!)",
    re.IGNORECASE,
)

DIRETIVAS_DART = re.compile(
    r"^//+\s*(ignore:|ignore_for_file:|coverage:|design-exception:)",
    re.IGNORECASE,
)

PASTAS_IGNORADAS = {
    ".git",
    ".dart_tool",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "node_modules",
    ".idea",
    ".vscode",
    "android",
    "ios",
    "web",
    "linux",
    "macos",
    "windows",
}

ALVOS_PADRAO = ("backend", "mobile/lib", "mobile/test", "mobile/tool")


@dataclass
class Resultado:
    arquivos: int = 0
    alterados: int = 0
    removidos: int = 0
    preservados: int = 0
    docstrings: int = 0
    falhas: list[str] = field(default_factory=list)

    def somar(self, outro: Resultado) -> None:
        self.arquivos += outro.arquivos
        self.alterados += outro.alterados
        self.removidos += outro.removidos
        self.preservados += outro.preservados
        self.docstrings += outro.docstrings
        self.falhas += outro.falhas


# ----------------------------------------------------------------------------- Python


def _fatias_de_comentario_py(fonte: str, tudo: bool) -> tuple[list[tuple[int, int, int]], int]:
    """As fatias `(linha, coluna_inicial, coluna_final)` a remover, e quantas ficaram.

    Usa `tokenize`, e não expressão regular: só ele distingue um `#` de comentário de um `#`
    dentro de literal, que é o erro que apaga código.
    """
    fatias: list[tuple[int, int, int]] = []
    preservados = 0

    leitor = io.StringIO(fonte).readline
    for token in tokenize.generate_tokens(leitor):
        if token.type != tokenize.COMMENT:
            continue
        if not tudo and DIRETIVAS_PY.match(token.string.strip()):
            preservados += 1
            continue
        fatias.append((token.start[0], token.start[1], token.end[1]))

    return fatias, preservados


def _docstrings_py(fonte: str) -> list[tuple[int, int]]:
    """As linhas `(inicio, fim)` de cada docstring, 1-indexadas e inclusivas."""
    import ast

    arvore = ast.parse(fonte)
    fatias: list[tuple[int, int]] = []

    for no in ast.walk(arvore):
        if not isinstance(
            no, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        corpo = getattr(no, "body", None)
        if not corpo:
            continue
        primeiro = corpo[0]
        if (
            isinstance(primeiro, ast.Expr)
            and isinstance(primeiro.value, ast.Constant)
            and isinstance(primeiro.value.value, str)
        ):
            # Docstring que é o corpo inteiro vira `pass`, senão o arquivo não compila.
            if len(corpo) == 1:
                continue
            fatias.append((primeiro.lineno, primeiro.end_lineno or primeiro.lineno))

    return fatias


def limpar_python(fonte: str, tudo: bool, docstrings: bool) -> tuple[str, int, int, int]:
    fatias, preservados = _fatias_de_comentario_py(fonte, tudo)

    linhas = fonte.splitlines(keepends=True)
    remover_linha: set[int] = set()

    for linha, inicio, _fim in sorted(fatias, reverse=True):
        i = linha - 1
        antes = linhas[i][:inicio]
        if antes.strip() == "":
            remover_linha.add(i)
        else:
            quebra = "\n" if linhas[i].endswith("\n") else ""
            linhas[i] = antes.rstrip() + quebra

    doc_removidas = 0
    if docstrings:
        for inicio, fim in _docstrings_py(fonte):
            for n in range(inicio - 1, fim):
                remover_linha.add(n)
            doc_removidas += 1

    saida: list[str] = []
    for i, linha in enumerate(linhas):
        if i in remover_linha:
            continue
        saida.append(linha)

    return "".join(saida), len(fatias), preservados, doc_removidas


# ------------------------------------------------------------------------------- Dart


def _varrer_dart(fonte: str) -> list[tuple[int, int, bool]]:
    """As fatias `(inicio, fim, de_linha)` de cada comentário, em índice de caractere.

    Escrito à mão porque não há lexer de Dart aqui, e porque o que importa é **não** confundir
    comentário com texto: `'https://fiance.app'` tem `//` dentro de uma string, e um regex o
    apagaria junto com metade da URL.

    Trata aspas simples e duplas, triplas, string crua (`r'...'`), escape, comentário de bloco
    aninhado (Dart permite) e interpolação `${...}`, que volta a ser código dentro da string.
    """
    fatias: list[tuple[int, int, bool]] = []

    i = 0
    n = len(fonte)

    # Pilha de contextos de string abertos por interpolação. Cada item é (fechamento, cru).
    pilha: list[tuple[str, bool]] = []
    chaves: list[int] = []

    fechamento: str | None = None
    cru = False

    while i < n:
        c = fonte[i]

        if fechamento is not None:
            if not cru and c == "\\":
                i += 2
                continue
            if c == "$" and i + 1 < n and fonte[i + 1] == "{":
                pilha.append((fechamento, cru))
                chaves.append(0)
                fechamento, cru = None, False
                i += 2
                continue
            if fonte.startswith(fechamento, i):
                i += len(fechamento)
                fechamento = None
                continue
            i += 1
            continue

        if pilha and c == "{":
            chaves[-1] += 1
            i += 1
            continue
        if pilha and c == "}":
            if chaves[-1] == 0:
                fechamento, cru = pilha.pop()
                chaves.pop()
                i += 1
                continue
            chaves[-1] -= 1
            i += 1
            continue

        if fonte.startswith("//", i):
            fim = fonte.find("\n", i)
            fim = n if fim == -1 else fim
            fatias.append((i, fim, True))
            i = fim
            continue

        if fonte.startswith("/*", i):
            profundidade = 1
            j = i + 2
            while j < n and profundidade:
                if fonte.startswith("/*", j):
                    profundidade += 1
                    j += 2
                elif fonte.startswith("*/", j):
                    profundidade -= 1
                    j += 2
                else:
                    j += 1
            fatias.append((i, j, False))
            i = j
            continue

        aspas = None
        salto = 0
        if c == "r" and i + 1 < n and fonte[i + 1] in "'\"":
            aspas, salto, ehcru = fonte[i + 1], 2, True
        elif c in "'\"":
            aspas, salto, ehcru = c, 1, False

        if aspas:
            base = i + salto - 1
            tripla = aspas * 3
            if fonte.startswith(tripla, base):
                fechamento = tripla
                i = base + 3
            else:
                fechamento = aspas
                i = base + 1
            cru = ehcru
            continue

        i += 1

    return fatias


def limpar_dart(fonte: str, tudo: bool) -> tuple[str, int, int]:
    fatias = _varrer_dart(fonte)

    remover: list[tuple[int, int]] = []
    preservados = 0

    for inicio, fim, _de_linha in fatias:
        texto = fonte[inicio:fim].strip()
        if not tudo and DIRETIVAS_DART.match(texto):
            preservados += 1
            continue
        remover.append((inicio, fim))

    if not remover:
        return fonte, 0, preservados

    saida = fonte
    for inicio, fim in sorted(remover, reverse=True):
        saida = saida[:inicio] + saida[fim:]

    # Uma linha que existia só para o comentário some; uma que tinha código antes dele fica sem o
    # espaço solto no fim.
    linhas = saida.split("\n")
    originais = fonte.split("\n")
    apagadas = {i for i, linha in enumerate(originais) if linha.strip().startswith(("//", "/*"))}

    resultado: list[str] = []
    for i, linha in enumerate(linhas):
        limpa = linha.rstrip()
        if limpa == "" and i in apagadas:
            continue
        resultado.append(limpa)

    return "\n".join(resultado), len(remover), preservados


# ------------------------------------------------------------------------------ arquivo


def processar(caminho: Path, tudo: bool, docstrings: bool, aplicar: bool) -> Resultado:
    r = Resultado(arquivos=1)
    original = caminho.read_text(encoding="utf-8")

    try:
        if caminho.suffix == ".py":
            novo, removidos, preservados, docs = limpar_python(original, tudo, docstrings)
            r.docstrings = docs
        else:
            novo, removidos, preservados = limpar_dart(original, tudo)
            if original.endswith("\n") and not novo.endswith("\n"):
                novo += "\n"
    except Exception as exc:
        r.falhas.append(f"{caminho}: {type(exc).__name__}: {exc}")
        return r

    r.removidos = removidos
    r.preservados = preservados

    if novo != original:
        r.alterados = 1
        if aplicar:
            caminho.write_text(novo, encoding="utf-8")

    return r


def coletar(raizes: list[Path]) -> list[Path]:
    arquivos: list[Path] = []
    for raiz in raizes:
        if raiz.is_file():
            arquivos.append(raiz)
            continue
        for caminho in sorted(raiz.rglob("*")):
            if caminho.suffix not in (".py", ".dart"):
                continue
            if any(parte in PASTAS_IGNORADAS for parte in caminho.parts):
                continue
            arquivos.append(caminho)
    return arquivos


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("alvos", nargs="*", default=list(ALVOS_PADRAO))
    p.add_argument("--aplicar", action="store_true", help="escreve; sem isto é só relatório")
    p.add_argument(
        "--tudo",
        action="store_true",
        help="remove também noqa, type:, pragma:, ignore: e design-exception: — quebra a esteira",
    )
    p.add_argument(
        "--docstrings",
        action="store_true",
        help="remove também docstring de Python (some do OpenAPI e de __doc__)",
    )
    args = p.parse_args(argv)

    raizes = [Path(a) for a in (args.alvos or ALVOS_PADRAO)]
    ausentes = [r for r in raizes if not r.exists()]
    if ausentes:
        print("caminho inexistente: " + ", ".join(str(a) for a in ausentes), file=sys.stderr)
        return 2

    total = Resultado()
    for caminho in coletar(raizes):
        total.somar(processar(caminho, args.tudo, args.docstrings, args.aplicar))

    modo = "aplicado" if args.aplicar else "simulação (use --aplicar para escrever)"
    print(f"{modo}")
    print(f"  arquivos varridos   {total.arquivos}")
    print(f"  arquivos alterados  {total.alterados}")
    print(f"  comentários             {total.removidos}")
    if total.docstrings:
        print(f"  docstrings              {total.docstrings}")
    print(f"  diretivas preservadas   {total.preservados}")

    if total.preservados and not args.tudo:
        print("\n  diretivas ficam porque são lidas por máquina: noqa, type:, pragma:, fmt:,")
        print("  ruff:, mypy:, isort:, nosec, shebang, ignore:, ignore_for_file:, coverage: e")
        print("  design-exception:. Use --tudo para removê-las e consertar a esteira à mão.")

    if total.falhas:
        print("\nfalhas:", file=sys.stderr)
        for f in total.falhas:
            print("  " + f, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
