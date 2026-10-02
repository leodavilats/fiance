from __future__ import annotations

import re
from pathlib import Path

from app.analysis.texto import numero, numero_com_sinal, reais

APP = Path(__file__).resolve().parents[1] / "app"

DECIMAL_EM_F_STRING = re.compile(r"\{[^{}]*:[+,]?\.[1-9]f\}")


def test_nenhuma_frase_do_backend_escreve_decimal_com_ponto():
    achados = []
    for arquivo in sorted(APP.rglob("*.py")):
        if arquivo.name == "texto.py" and arquivo.parent.name == "analysis":
            continue
        for numero_da_linha, linha in enumerate(
            arquivo.read_text(encoding="utf-8").splitlines(), 1
        ):
            if DECIMAL_EM_F_STRING.search(linha):
                achados.append(f"{arquivo.relative_to(APP)}:{numero_da_linha}: {linha.strip()}")

    assert achados == [], (
        "frase com decimal em f-string sai com ponto ('14.90%', 'R$ 20,000') e chega à tela "
        "assim; use reais(), numero() ou numero_com_sinal() de analysis/texto.py:\n"
        + "\n".join(achados)
    )


def test_os_formatadores_escrevem_em_portugues():
    assert reais(20000) == "R$ 20.000,00"
    assert numero(14.9) == "14,90"
    assert numero(1234.5, 1) == "1.234,5"
    assert numero_com_sinal(11.54) == "+11,5"
    assert numero_com_sinal(-4.2) == "-4,2"
    assert numero_com_sinal(0) == "0,0"
