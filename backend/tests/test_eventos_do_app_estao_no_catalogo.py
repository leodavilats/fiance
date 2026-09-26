from __future__ import annotations

import pathlib
import re

import pytest

from app.core.events import AHA_EVENTS, catalog_as_dicts

_APP = pathlib.Path(__file__).resolve().parents[2] / "mobile" / "lib"

_CHAMADA = re.compile(r"""(?:trackEvent\(\s*context,\s*|\.track\(\s*)'([a-z_]+)'""")


def _eventos_do_app() -> set[str]:
    nomes: set[str] = set()
    for arquivo in _APP.rglob("*.dart"):
        nomes |= set(_CHAMADA.findall(arquivo.read_text(encoding="utf-8")))
    return nomes


@pytest.mark.skipif(not _APP.exists(), reason="repositório sem a pasta mobile")
def test_todo_evento_que_o_app_envia_esta_no_catalogo():
    catalogo = {e["name"] for e in catalog_as_dicts()}
    enviados = _eventos_do_app()

    assert enviados, "o app deixou de enviar eventos: o funil de produto fica cego"
    assert enviados <= catalogo, (
        f"evento fora do dicionário: {sorted(enviados - catalogo)}. O servidor devolve 422 para "
        "nome desconhecido, e a telemetria descarta a falha em silêncio: o evento some"
    )


def test_os_eventos_de_aha_existem_no_catalogo():
    assert set(AHA_EVENTS) <= {e["name"] for e in catalog_as_dicts()}
