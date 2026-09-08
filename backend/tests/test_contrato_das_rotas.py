from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.main import app

GOLDEN = Path(__file__).parent / "contrato_das_rotas.json"

METODOS = ("get", "post", "put", "patch", "delete")

SEM_MODELO_HOJE = 45


def _campos(schema: dict, componentes: dict, visitados: frozenset[str] = frozenset()) -> list[str]:
    ref = schema.get("$ref")
    if ref:
        nome = ref.rsplit("/", 1)[-1]
        if nome in visitados:
            return []
        alvo = componentes.get(nome, {})
        return _campos(alvo, componentes, visitados | {nome})

    for combinador in ("allOf", "anyOf", "oneOf"):
        if combinador in schema:
            juntos: list[str] = []
            for parte in schema[combinador]:
                juntos.extend(_campos(parte, componentes, visitados))
            return sorted(set(juntos))

    if schema.get("type") == "array":
        return _campos(schema.get("items", {}), componentes, visitados)

    return sorted(schema.get("properties", {}))


def _schema_de_sucesso(operacao: dict) -> dict:
    """O corpo da resposta de sucesso — que em rota de escrita é 201, não 200."""
    respostas = operacao.get("responses", {})
    for codigo in sorted(c for c in respostas if c.startswith("2")):
        schema = respostas[codigo].get("content", {}).get("application/json", {}).get("schema", {})
        if schema:
            return schema
    return {}


def contrato_atual() -> dict[str, list[str]]:
    openapi = app.openapi()
    componentes = openapi.get("components", {}).get("schemas", {})
    saida: dict[str, list[str]] = {}

    for caminho, operacoes in openapi.get("paths", {}).items():
        if not caminho.startswith("/api/v1/"):
            continue
        for metodo, operacao in operacoes.items():
            if metodo not in METODOS:
                continue
            corpo = _schema_de_sucesso(operacao)
            campos = _campos(corpo, componentes)
            if campos:
                saida[f"{metodo.upper()} {caminho}"] = campos

    return saida


@pytest.fixture(scope="module")
def atual():
    return contrato_atual()


@pytest.fixture(scope="module")
def registrado():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


class TestNenhumCampoSomeEmSilencio:
    def test_nenhuma_rota_perdeu_campo(self, atual, registrado):
        perdidos = {}
        for rota, campos in registrado.items():
            if rota not in atual:
                continue
            faltando = sorted(set(campos) - set(atual[rota]))
            if faltando:
                perdidos[rota] = faltando

        assert perdidos == {}, (
            "campo declarado sumiu do modelo de resposta: o FastAPI descarta em "
            "silêncio o que o response_model não declara. Se a remoção é intencional, "
            "atualize tests/contrato_das_rotas.json no mesmo commit."
        )

    def test_nenhuma_rota_sumiu(self, atual, registrado):
        sumidas = sorted(set(registrado) - set(atual))

        assert sumidas == [], (
            "rota registrada não existe mais: se foi removida de propósito, "
            "atualize tests/contrato_das_rotas.json no mesmo commit."
        )

    def test_rota_nova_precisa_entrar_no_registro(self, atual, registrado):
        novas = sorted(set(atual) - set(registrado))

        assert novas == [], (
            "rota nova sem contrato registrado: rode "
            "`python -m tests.contrato_das_rotas` e confira o diff."
        )


def _devolve_json(operacao: dict) -> bool:
    """Se a rota responde JSON — a única forma de resposta que tem campos.

    Uma rota binária (a imagem de compartilhamento por ticker, por exemplo) não
    tem campo nenhum a sumir em silêncio, que é a classe de bug que o contrato
    existe para pegar. Contá-la como "rota sem modelo" faria a catraca subir por
    um motivo que ela não mede.
    """
    respostas = operacao.get("responses", {})
    houve_2xx = False

    for codigo, corpo in respostas.items():
        if not str(codigo).startswith("2"):
            continue
        houve_2xx = True
        content = corpo.get("content", {})
        if not content:
            continue
        return any(tipo.startswith("application/json") for tipo in content)

    # Rota de 204: teve resposta de sucesso e nenhuma delas declara corpo. Não há campo a
    # sumir, pelo mesmo motivo da rota binária — contá-la faria a catraca subir por um motivo
    # que ela não mede. Sem 2xx nenhum a resposta é desconhecida, e aí a catraca é estrita.
    return not houve_2xx


def rotas_declaradas() -> set[str]:
    todas: set[str] = set()
    for caminho, operacoes in app.openapi().get("paths", {}).items():
        if not caminho.startswith("/api/v1/"):
            continue
        for metodo, operacao in operacoes.items():
            if metodo in METODOS and _devolve_json(operacao):
                todas.add(f"{metodo.upper()} {caminho}")
    return todas


class TestOContratoEUtil:
    def test_o_registro_cobre_as_rotas_da_carteira(self, registrado):
        criticas = {
            "GET /api/v1/portfolio",
            "POST /api/v1/portfolio/position",
            "POST /api/v1/portfolio/sell",
            "DELETE /api/v1/portfolio/position/{ticker}",
        }

        assert criticas <= set(registrado)

    def test_a_lista_de_rotas_sem_modelo_nao_cresce(self, atual):
        sem_modelo = sorted(rotas_declaradas() - set(atual))

        assert len(sem_modelo) <= SEM_MODELO_HOJE, (
            "rota nova devolvendo dict solto: sem response_model o FastAPI não "
            "garante contrato nenhum, e campo que some não falha em lugar algum. "
            "Declare um modelo, ou ajuste SEM_MODELO_HOJE sabendo o que está abrindo mão."
        )

    def test_a_analise_declara_o_veredito_e_o_que_o_derrubaria(self, atual):
        campos = set(atual.get("GET /api/v1/asset/{symbol}", []))

        assert {"decision", "fair_price", "price_history"} <= campos
