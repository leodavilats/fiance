"""Entitlement: a régua, o teto, o trial e as duas regras de arquitetura.

A composição do plano é a decisão mais provável de ser revista depois dos
primeiros experimentos — e a mais difícil de reverter depois de publicada. Estes
testes cobrem menos o *conteúdo* da régua e mais a *propriedade* de que ela é
um lugar só, mudável por configuração.
"""

from __future__ import annotations

import time

import pytest

from app.core.config import get_settings
from app.entitlement import Feature, Plan, check, meter, plans, resolve
from app.entitlement.resolve import TRIAL_DAYS
from app.services import subscription_service
from tests.conftest import make_auth_headers

DAY = 86400.0


@pytest.fixture()
def regua_ligada(monkeypatch):
    """A régua roda desligada em produção hoje; ligá-la é uma decisão."""
    settings = get_settings()
    monkeypatch.setattr(settings, "entitlements_enabled", True, raising=False)
    return settings


class TestFlagDesligada:
    def test_sem_a_flag_todo_mundo_tem_tudo(self):
        """É o estado de hoje: o código existe, a cobrança não."""
        direitos = resolve("u_ent_off")

        assert direitos.unrestricted is True
        assert all(direitos.features.values())
        assert all(limite is None for limite in direitos.limits.values())

    def test_sem_a_flag_nenhuma_verificacao_bloqueia(self):
        for feature in Feature:
            assert check(feature, "u_ent_off_all").allowed is True

    def test_sem_a_flag_o_contador_nao_roda(self):
        """Perguntar não pode gastar cota que nem está sendo cobrada."""
        for _ in range(20):
            check(Feature.ASSET_PAGE, "u_ent_off_meter", cost=1)

        assert meter.used("u_ent_off_meter", Feature.ASSET_PAGE) == 0


class TestRegua:
    def test_a_regua_e_dado_e_traz_o_motivo(self):
        regras = {r["feature"]: r for r in plans.as_dicts()}

        assert regras["strategy"]["min_plan"] == "premium"
        assert regras["portfolio"]["min_plan"] == "free"
        assert all(r["rationale"] for r in regras.values()), "toda linha precisa ser defensável"

    def test_o_que_nunca_e_pago_esta_declarado_como_livre(self):
        """Não é 'ainda não cercado': é decisão registrada."""
        for feature in (
            Feature.PORTFOLIO,
            Feature.PORTFOLIO_SUMMARY,
            Feature.ACCOUNT_EXPORT,
            Feature.DIVIDENDS_RECEIVED,
        ):
            assert plans.allows(feature, Plan.FREE), feature

    def test_a_regua_nao_sabe_expressar_cerca_proibida(self):
        """Número de ativos e exportação não têm representação aqui.

        Não por esquecimento: uma cerca que não pode ser escrita é uma cerca que
        não pode ser acidentalmente ligada.
        """
        nomes = {f.value for f in Feature}

        assert "portfolio_max_assets" not in nomes
        assert plans.limit_for(Feature.PORTFOLIO, Plan.FREE) is None
        assert plans.limit_for(Feature.ACCOUNT_EXPORT, Plan.FREE) is None

    def test_mudar_a_regua_e_mudar_um_valor(self, regua_ligada, monkeypatch):
        """A propriedade que justifica o módulo existir."""
        assert check(Feature.STRATEGY, "u_ent_regua").allowed is False

        monkeypatch.setitem(
            plans.RULES,
            Feature.STRATEGY,
            plans.Rule(Feature.STRATEGY, Plan.FREE, rationale="experimento"),
        )

        assert check(Feature.STRATEGY, "u_ent_regua").allowed is True


class TestPlanoEBloqueio:
    def test_conta_nova_e_free(self, regua_ligada):
        assert resolve("u_ent_novo").plan is Plan.FREE

    def test_feature_premium_bloqueia_no_free_com_o_motivo(self, regua_ligada):
        decisao = check(Feature.STRATEGY, "u_ent_free")

        assert decisao.allowed is False
        assert decisao.limit_reached is False
        assert decisao.reason
        assert decisao.as_dict()["required_plan"] == "premium"

    def test_a_resposta_diz_qual_plano_falta(self, regua_ligada, client):
        headers = make_auth_headers("u_ent_402")

        resposta = client.get("/api/entitlements/check/strategy", headers=headers)

        corpo = resposta.json()
        assert corpo["allowed"] is False
        assert corpo["required_plan"] == "premium"

    def test_assinatura_ativa_libera(self, regua_ligada):
        subscription_service.grant("u_ent_pago", "premium", 1990)

        assert resolve("u_ent_pago").plan is Plan.PREMIUM
        assert check(Feature.STRATEGY, "u_ent_pago").allowed is True

    def test_assinatura_cancelada_degrada_sem_apagar(self, regua_ligada, client):
        """Cancelar Premium não é cancelar conta."""
        headers = make_auth_headers("u_ent_churn")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )
        subscription_service.grant("u_ent_churn", "premium", 1990)
        subscription_service.cancel("u_ent_churn", reason="teste")

        assert resolve("u_ent_churn").plan is Plan.FREE
        assert client.get("/api/portfolio", headers=headers).json()["items"] != []

    def test_periodo_vencido_degrada(self, regua_ligada):
        subscription_service.grant("u_ent_vencido", "premium", 1990, period_end=time.time() - DAY)

        assert resolve("u_ent_vencido").plan is Plan.FREE


class TestTeto:
    def test_o_teto_mensal_bloqueia_depois_de_consumido(self, regua_ligada):
        limite = plans.limit_for(Feature.ASSET_PAGE, Plan.FREE)

        for _ in range(limite):
            assert check(Feature.ASSET_PAGE, "u_ent_teto", cost=1).allowed is True

        bloqueado = check(Feature.ASSET_PAGE, "u_ent_teto", cost=1)
        assert bloqueado.allowed is False
        assert bloqueado.limit_reached is True
        assert str(limite) in bloqueado.reason

    def test_perguntar_nao_consome(self, regua_ligada):
        """A tela pergunta para saber se desenha o gate."""
        for _ in range(50):
            check(Feature.ASSET_PAGE, "u_ent_peek", cost=0)

        assert meter.used("u_ent_peek", Feature.ASSET_PAGE) == 0

    def test_o_teto_e_por_usuario(self, regua_ligada):
        limite = plans.limit_for(Feature.ASSET_PAGE, Plan.FREE)
        for _ in range(limite + 2):
            check(Feature.ASSET_PAGE, "u_ent_teto_a", cost=1)

        assert check(Feature.ASSET_PAGE, "u_ent_teto_b", cost=1).allowed is True

    def test_teto_permanente_libera_vaga_ao_devolver(self, regua_ligada):
        """Três alertas são três alertas: apagar um libera o lugar."""
        limite = plans.limit_for(Feature.PRICE_ALERTS, Plan.FREE)
        for _ in range(limite):
            check(Feature.PRICE_ALERTS, "u_ent_alerta", cost=1)

        assert check(Feature.PRICE_ALERTS, "u_ent_alerta", cost=1).allowed is False

        meter.release("u_ent_alerta", Feature.PRICE_ALERTS)

        assert check(Feature.PRICE_ALERTS, "u_ent_alerta", cost=1).allowed is True

    def test_consumo_mensal_nao_devolve_vaga(self, regua_ligada):
        """Devolver cota de página já vista daria acesso ilimitado a quem recarrega."""
        check(Feature.ASSET_PAGE, "u_ent_mensal", cost=1)

        meter.release("u_ent_mensal", Feature.ASSET_PAGE)

        assert meter.used("u_ent_mensal", Feature.ASSET_PAGE) == 1

    def test_premium_sem_teto_onde_a_regua_diz_sem_teto(self, regua_ligada):
        subscription_service.grant("u_ent_ilimitado", "premium", 1990)

        for _ in range(30):
            assert check(Feature.ASSET_PAGE, "u_ent_ilimitado", cost=1).allowed is True


class TestTrial:
    def test_o_trial_comeca_na_primeira_posicao_e_nao_no_cadastro(self, regua_ligada, client):
        headers = make_auth_headers("u_ent_trial")

        antes = subscription_service.get("u_ent_trial")
        assert antes["trial_started_at"] is None

        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        depois = subscription_service.get("u_ent_trial")
        assert depois["trial_started_at"] is not None
        assert depois["trial_ends_at"] == pytest.approx(
            depois["trial_started_at"] + TRIAL_DAYS * DAY
        )

    def test_durante_o_trial_a_pessoa_e_premium(self, regua_ligada, client):
        headers = make_auth_headers("u_ent_trial_premium")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        direitos = resolve("u_ent_trial_premium")

        assert direitos.plan is Plan.PREMIUM
        assert direitos.in_trial is True
        assert (
            direitos.days_left_in_trial == TRIAL_DAYS - 1
            or direitos.days_left_in_trial == TRIAL_DAYS
        )

    def test_o_trial_nao_reinicia_na_segunda_posicao(self, regua_ligada, client):
        headers = make_auth_headers("u_ent_trial_uma_vez")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )
        primeiro = subscription_service.get("u_ent_trial_uma_vez")["trial_started_at"]

        client.post(
            "/api/portfolio/position",
            json={"ticker": "VALE3", "quantity": 50, "avg_price": 60.0},
            headers=headers,
        )

        assert subscription_service.get("u_ent_trial_uma_vez")["trial_started_at"] == primeiro

    def test_trial_vencido_volta_para_free(self, regua_ligada):
        subscription_service.start_trial("u_ent_trial_fim", now=time.time() - 30 * DAY)

        assert resolve("u_ent_trial_fim").plan is Plan.FREE
        assert resolve("u_ent_trial_fim").in_trial is False


class TestPrecoTravado:
    def test_o_preco_contratado_e_gravado_e_nao_derivado(self):
        subscription_service.grant(
            "u_ent_fundador", "premium", 14990, interval="yearly", locked=True
        )

        assinatura = subscription_service.get("u_ent_fundador")

        assert assinatura["price_cents"] == 14990
        assert assinatura["locked"] is True

    def test_reajuste_da_tabela_nao_alcanca_quem_esta_travado(self, monkeypatch):
        """A promessa é pública, então tem que ser dado — não memória."""
        subscription_service.grant("u_ent_travado", "premium", 14990, locked=True)

        monkeypatch.setattr(subscription_service, "PRICE_MONTHLY_CENTS", 2990)

        assert subscription_service.get("u_ent_travado")["price_cents"] == 14990


class TestWebhookIdempotente:
    def test_o_mesmo_evento_so_e_processado_uma_vez(self):
        """O provedor reenvia até receber 200, por desenho."""
        assert subscription_service.already_processed("stripe", "evt_1") is False

        subscription_service.mark_processed("stripe", "evt_1", "assinatura criada")

        assert subscription_service.already_processed("stripe", "evt_1") is True

    def test_marcar_duas_vezes_nao_falha(self):
        subscription_service.mark_processed("stripe", "evt_2")
        subscription_service.mark_processed("stripe", "evt_2")

        assert subscription_service.already_processed("stripe", "evt_2") is True

    def test_provedores_tem_espacos_de_id_separados(self):
        subscription_service.mark_processed("stripe", "evt_3")

        assert subscription_service.already_processed("play", "evt_3") is False


class TestArquitetura:
    def test_analise_e_otimizador_nao_conhecem_entitlement(self):
        """Se o cálculo souber quem paga, a independência vira promessa.

        Nenhuma entrada comercial entra no score, no preço justo ou na
        ordenação — e a forma de garantir isso é a dependência não existir.
        """
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent / "app"
        infratores = []

        for pasta in ("analysis", "optimizer", "collectors", "ledger"):
            for arquivo in (raiz / pasta).rglob("*.py"):
                texto = arquivo.read_text(encoding="utf-8")
                if "entitlement" in texto or "subscription" in texto:
                    infratores.append(str(arquivo.relative_to(raiz)))

        assert infratores == [], f"dependência comercial no cálculo: {infratores}"

    def test_nenhuma_condicional_de_plano_fora_do_modulo(self):
        """Cerca espalhada é impossível de mudar depois."""
        import pathlib
        import re

        raiz = pathlib.Path(__file__).resolve().parent.parent / "app"
        padrao = re.compile(
            r"if\s+.*\b(is_premium|premium\b|is_paid|plano\s*==|plan\s*==)", re.IGNORECASE
        )

        infratores = []
        for arquivo in raiz.rglob("*.py"):
            relativo = arquivo.relative_to(raiz)
            if relativo.parts[0] == "entitlement":
                continue
            for numero, linha in enumerate(
                arquivo.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if padrao.search(linha):
                    infratores.append(f"{relativo}:{numero}: {linha.strip()}")

        assert infratores == [], "condicional de plano fora de app/entitlement:\n" + "\n".join(
            infratores
        )
