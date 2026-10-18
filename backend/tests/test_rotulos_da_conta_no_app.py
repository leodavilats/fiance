from __future__ import annotations

import pathlib
import re

from app.storage.account_store import USER_SCOPED_MODELS

VOCABULARIO = pathlib.Path(__file__).resolve().parents[2] / "mobile/lib/core/vocabulary.dart"


def test_toda_tabela_apagada_com_a_conta_tem_nome_no_aplicativo():
    fonte = VOCABULARIO.read_text(encoding="utf-8")
    bloco = fonte[fonte.index("const Map<String, String> fiAccountData") :]
    rotulos = set(re.findall(r"'(\w+)':", bloco[: bloco.index("};")]))

    sem_nome = sorted({label for label, _ in USER_SCOPED_MODELS} - rotulos)

    assert sem_nome == [], (
        "a tela de excluir conta lista o que será apagado pelo nome de fiAccountData; tabela "
        f"sem entrada lá aparece crua para a pessoa: {sem_nome}"
    )
