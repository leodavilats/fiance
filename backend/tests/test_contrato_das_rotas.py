from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.main import app

GOLDEN = Path(__file__).parent / "contrato_das_rotas.json"

METODOS = ("get", "post", "put", "patch", "delete")

SEM_MODELO_HOJE = 10


PROFUNDIDADE = 4


def _resolver(schema: dict, componentes: dict, visitados: frozenset[str]):
    ref = schema.get("$ref")
    if not ref:
        return schema, visitados
    nome = ref.rsplit("/", 1)[-1]
    if nome in visitados:
        return {}, visitados
    return _resolver(componentes.get(nome, {}), componentes, visitados | {nome})


def _campos(
    schema: dict,
    componentes: dict,
    visitados: frozenset[str] = frozenset(),
    prefixo: str = "",
    profundidade: int = 0,
    marcar_obrigatorio: bool = False,
) -> list[str]:
    schema, visitados = _resolver(schema, componentes, visitados)

    for combinador in ("allOf", "anyOf", "oneOf"):
        if combinador in schema:
            juntos: list[str] = []
            for parte in schema[combinador]:
                juntos.extend(
                    _campos(
                        parte, componentes, visitados, prefixo, profundidade, marcar_obrigatorio
                    )
                )
            return sorted(set(juntos))

    if schema.get("type") == "array":
        return _campos(
            schema.get("items", {}),
            componentes,
            visitados,
            f"{prefixo}[]" if prefixo else prefixo,
            profundidade,
            marcar_obrigatorio,
        )

    obrigatorios = set(schema.get("required", [])) if marcar_obrigatorio else set()
    saida: list[str] = []
    for nome, filho in schema.get("properties", {}).items():
        caminho = f"{prefixo}.{nome}" if prefixo else nome
        saida.append(f"{caminho}!" if nome in obrigatorios else caminho)
        if profundidade + 1 < PROFUNDIDADE:
            saida.extend(
                _campos(
                    filho, componentes, visitados, caminho, profundidade + 1, marcar_obrigatorio
                )
            )
    return sorted(set(saida))


def _schema_de_entrada(operacao: dict) -> dict:
    corpo = operacao.get("requestBody", {}).get("content", {})
    return corpo.get("application/json", {}).get("schema", {})


def _schema_de_sucesso(operacao: dict) -> dict:
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
            entrada = _campos(_schema_de_entrada(operacao), componentes, marcar_obrigatorio=True)
            if entrada:
                saida[f"{metodo.upper()} {caminho} (entrada)"] = entrada

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
            "campo declarado sumiu do contrato. Na resposta, o FastAPI descarta em silêncio o "
            "que o response_model não declara; na entrada (rotas com '(entrada)'), o servidor "
            "passa a ignorar o que o app manda, e um nome que ganhou '!' virou obrigatório e "
            "quebra quem não o envia. Se é intencional, rode `python -m tests.contrato_das_rotas` "
            "no mesmo commit."
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

    def test_o_registro_desce_aos_campos_aninhados(self, atual):
        campos = set(atual.get("GET /api/v1/asset/{symbol}", []))

        assert {"fair_price.principal_value", "fair_price.fair_low", "decision.label"} <= campos, (
            "o preço justo vem aninhado na análise: registrando só o nível de cima, a troca de "
            "consensus por principal_value passou sem que o contrato visse"
        )

    def test_o_registro_guarda_o_que_o_app_envia(self, atual):
        entrada = set(atual.get("POST /api/v1/portfolio/position (entrada)", []))

        assert {"ticker!", "quantity!", "avg_price!"} <= entrada, (
            "campo que o app envia e o servidor deixa de ler é ignorado em silêncio, e campo que "
            "vira obrigatório quebra quem não o envia"
        )
