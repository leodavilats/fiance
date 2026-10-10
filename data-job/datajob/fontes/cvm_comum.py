from __future__ import annotations

import csv
import io
import re
import unicodedata
import zipfile
from datetime import date

from datajob.erros import ArquivoInvalido


def ler_csv(conteudo: bytes, colunas: set[str]) -> list[dict[str, str]]:
    leitor = csv.DictReader(io.StringIO(conteudo.decode("latin-1")), delimiter=";")
    faltando = colunas - set(leitor.fieldnames or ())
    if faltando:
        raise ArquivoInvalido(f"Faltam colunas no CSV da CVM: {sorted(faltando)}.")
    return [{k: (v or "").strip() for k, v in linha.items() if k} for linha in leitor]


def nomes_do_zip(conteudo: bytes) -> list[str]:
    try:
        with zipfile.ZipFile(io.BytesIO(conteudo)) as arquivo:
            return arquivo.namelist()
    except zipfile.BadZipFile as e:
        raise ArquivoInvalido("O conteúdo baixado não é um ZIP.") from e


def membro_do_zip(conteudo: bytes, nome: str) -> bytes:
    try:
        with zipfile.ZipFile(io.BytesIO(conteudo)) as arquivo:
            return arquivo.read(nome)
    except zipfile.BadZipFile as e:
        raise ArquivoInvalido("O conteúdo baixado não é um ZIP.") from e
    except KeyError as e:
        raise ArquivoInvalido(f"O ZIP não tem {nome}.") from e


def cnpj(texto: str) -> str | None:
    digitos = re.sub(r"\D", "", texto)
    if not digitos or set(digitos) == {"0"}:
        return None
    return digitos.zfill(14)


def data(texto: str) -> date | None:
    if not texto:
        return None
    try:
        return date.fromisoformat(texto[:10])
    except ValueError:
        return None


def nome_normalizado(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", sem_acento.upper())).strip()
