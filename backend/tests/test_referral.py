"""Indicação: código, atribuição, crédito — e as cercas contra abuso.

O que estes testes protegem não é o cálculo dos dias: é **quando** o crédito
sai. Um programa que credita no cadastro é uma máquina de imprimir Premium
apontada para o próprio caixa, e o erro só aparece na fatura.
"""

from __future__ import annotations

import time

import pytest

from app.entitlement import Plan, resolve
from app.services import referral_service
from tests.conftest import make_auth_headers


@pytest.fixture()
def regua_ligada(monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "entitlements_enabled", True, raising=False)


def _fingir_google(monkeypatch, user_id: str):
    """Troca a verificação do Google por uma identidade fixa.

    O login é o único ponto em que a atribuição acontece, então testá-lo exige
    passar por ele — e o token real depende de infraestrutura externa.
    """
    from app.api import auth as rota_auth
    from app.core.auth import GoogleUser

    monkeypatch.setattr(
        rota_auth,
        "verify_google_id_token",
        lambda _token: GoogleUser(
            sub=user_id, email=f"{user_id}@exemplo.com", name="Teste", picture=""
        ),
    )


def salvar_posicao(client, user_id: str, ticker: str = "PETR4"):
    return client.post(
        "/api/portfolio/position",
        json={"ticker": ticker, "quantity": 100, "avg_price": 30.0},
        headers=make_auth_headers(user_id),
    )


class TestCodigo:
    def test_o_codigo_e_estavel_entre_chamadas(self):
        """Um código que muda a cada consulta é um link quebrado no WhatsApp."""
        primeiro = referral_service.code_for("u_ref_estavel")
        segundo = referral_service.code_for("u_ref_estavel")

        assert primeiro == segundo

    def test_pessoas_diferentes_tem_codigos_diferentes(self):
        assert referral_service.code_for("u_ref_a") != referral_service.code_for("u_ref_b")

    def test_o_alfabeto_evita_o_que_se_confunde_lido_em_voz_alta(self):
        """O código é ditado por telefone e copiado de captura de tela."""
        codigo = referral_service.code_for("u_ref_alfabeto")

        assert not set(codigo) & set("O0I1L")

    def test_rotacionar_queima_o_antigo(self):
        antigo = referral_service.code_for("u_ref_rotaciona")
        novo = referral_service.rotate_code("u_ref_rotaciona")

        assert novo != antigo
        with pytest.raises(referral_service.ReferralError):
            referral_service.attribute("u_ref_orfao", antigo)


class TestCercasDaAtribuicao:
    def test_ninguem_se_indica(self):
        """O primeiro abuso que qualquer pessoa tenta, e o mais barato de
        bloquear."""
        codigo = referral_service.code_for("u_ref_self")

        with pytest.raises(referral_service.ReferralError, match="próprio código"):
            referral_service.attribute("u_ref_self", codigo)

    def test_uma_conta_e_atribuida_no_maximo_uma_vez(self):
        """Senão a mesma conta renderia crédito a cada amigo que a
        reivindicasse."""
        um = referral_service.code_for("u_ref_dono1")
        outro = referral_service.code_for("u_ref_dono2")
        referral_service.attribute("u_ref_disputado", um)

        with pytest.raises(referral_service.ReferralError, match="já foi atribuída"):
            referral_service.attribute("u_ref_disputado", outro)

    def test_quem_ja_tem_carteira_nao_pode_ser_reivindicado(self, client):
        """Aceitar depois deixaria alguém reivindicar um usuário que já estava
        no produto — crédito por uma aquisição que não aconteceu."""
        salvar_posicao(client, "u_ref_veterano")
        codigo = referral_service.code_for("u_ref_oportunista")

        with pytest.raises(referral_service.ReferralError, match="já tem carteira"):
            referral_service.attribute("u_ref_veterano", codigo)

    def test_codigo_inexistente_e_recusado(self):
        with pytest.raises(referral_service.ReferralError, match="não encontrado"):
            referral_service.attribute("u_ref_perdido", "ZZZZZZZZ")

    def test_codigo_vazio_e_recusado(self):
        with pytest.raises(referral_service.ReferralError):
            referral_service.attribute("u_ref_vazio", "   ")

    def test_o_codigo_e_aceito_sem_ligar_para_caixa_e_espaco(self):
        """Ele vem colado de uma mensagem, não digitado com cuidado."""
        codigo = referral_service.code_for("u_ref_caixa_dono")
        referral_service.attribute("u_ref_caixa", f"  {codigo.lower()} ")

        assert referral_service.status("u_ref_caixa_dono")["attributed"] == 1


class TestOCreditoSaiNaQualificacao:
    def test_atribuir_nao_credita_nada(self, regua_ligada):
        """Cadastro é grátis de fabricar aos milhares."""
        codigo = referral_service.code_for("u_ref_indicador")
        referral_service.attribute("u_ref_indicado", codigo)

        assert resolve("u_ref_indicador").plan is Plan.FREE
        assert referral_service.status("u_ref_indicador")["days_earned"] == 0

    def test_a_primeira_posicao_do_indicado_credita_os_dois_lados(self, client, regua_ligada):
        codigo = referral_service.code_for("u_ref_ganha")
        referral_service.attribute("u_ref_novato", codigo)

        salvar_posicao(client, "u_ref_novato")

        assert resolve("u_ref_ganha").plan is Plan.PREMIUM
        assert referral_service.status("u_ref_ganha")["qualified"] == 1

    def test_o_indicado_tambem_ganha(self, client, regua_ligada):
        """Um programa só para quem indica é um pedido de favor."""
        codigo = referral_service.code_for("u_ref_generoso")
        referral_service.attribute("u_ref_beneficiado", codigo)

        salvar_posicao(client, "u_ref_beneficiado")

        assert referral_service.status("u_ref_beneficiado")["credited_days_total"] == (
            referral_service.REWARD_DAYS
        )

    def test_qualificar_duas_vezes_nao_credita_duas_vezes(self, client, regua_ligada):
        """O modo de falha que ninguém percebe até a fatura."""
        codigo = referral_service.code_for("u_ref_unico")
        referral_service.attribute("u_ref_repetidor", codigo)

        salvar_posicao(client, "u_ref_repetidor", "PETR4")
        salvar_posicao(client, "u_ref_repetidor", "VALE3")
        referral_service.qualify("u_ref_repetidor")

        assert referral_service.status("u_ref_unico")["days_earned"] == (
            referral_service.REWARD_DAYS
        )

    def test_sem_indicacao_a_qualificacao_e_silenciosa(self, client):
        """A maioria das pessoas chega sozinha; isso não é caso de erro."""
        assert referral_service.qualify("u_ref_sozinho") is None


class TestCreditoAcumula:
    def test_duas_indicacoes_somam_dias(self, client, regua_ligada):
        """Creditar a partir de hoje apagaria o saldo de quem indicou duas
        pessoas na mesma semana."""
        codigo = referral_service.code_for("u_ref_soma")
        for indicado in ("u_ref_soma_a", "u_ref_soma_b"):
            referral_service.attribute(indicado, codigo)
            salvar_posicao(client, indicado)

        assert referral_service.status("u_ref_soma")["credited_days_total"] == (
            2 * referral_service.REWARD_DAYS
        )

    def test_o_credito_respeita_o_teto(self):
        """Crédito sem teto é passivo sem teto."""
        from app.core.database import db_session
        from app.models.db_models import SubscriptionDb

        agora = time.time()
        with db_session() as session:
            concedido = referral_service._credit(
                session, "u_ref_teto", referral_service.MAX_CREDITED_DAYS + 500, agora
            )
        assert concedido == referral_service.MAX_CREDITED_DAYS

        with db_session() as session:
            de_novo = referral_service._credit(session, "u_ref_teto", 30, agora)
            linha = session.get(SubscriptionDb, "u_ref_teto")
            total = linha.credited_days_total

        assert de_novo == 0
        assert total == referral_service.MAX_CREDITED_DAYS

    def test_o_credito_expira(self, regua_ligada):
        """Crédito é empréstimo de Premium, não upgrade permanente."""
        from app.core.database import db_session

        agora = time.time()
        with db_session() as session:
            referral_service._credit(session, "u_ref_expira", 30, agora)

        assert resolve("u_ref_expira").plan is Plan.PREMIUM
        assert resolve("u_ref_expira", now=agora + 31 * 86400).plan is Plan.FREE

    def test_o_credito_nao_reabre_o_trial(self, regua_ligada):
        """Trial é uma vez na vida; somá-los daria um segundo a quem já
        gastou o seu."""
        from app.core.database import db_session

        agora = time.time()
        from app.services import subscription_service

        subscription_service.start_trial("u_ref_trial", now=agora - 100 * 86400)
        with db_session() as session:
            referral_service._credit(session, "u_ref_trial", 30, agora)

        direitos = resolve("u_ref_trial")
        assert direitos.plan is Plan.PREMIUM
        assert direitos.in_trial is False


class TestRotas:
    def test_a_rota_devolve_o_codigo_e_as_contagens(self, client):
        headers = make_auth_headers("u_ref_rota")

        corpo = client.get("/api/referral", headers=headers).json()

        assert len(corpo["code"]) == 8
        assert corpo["reward_days"] == referral_service.REWARD_DAYS
        assert corpo["attributed"] == 0

    def test_a_rota_nunca_lista_quem_foi_indicado(self, client):
        """Quem clicou no link de alguém não escolheu aparecer numa tela dessa
        pessoa."""
        codigo = referral_service.code_for("u_ref_privacidade")
        referral_service.attribute("u_ref_anonimo", codigo)

        corpo = client.get("/api/referral", headers=make_auth_headers("u_ref_privacidade")).json()

        assert "u_ref_anonimo" not in str(corpo)
        assert corpo["attributed"] == 1

    def test_a_rota_de_rotacao_devolve_codigo_novo(self, client):
        headers = make_auth_headers("u_ref_rota_rot")
        antigo = client.get("/api/referral", headers=headers).json()["code"]

        novo = client.post("/api/referral/rotate", headers=headers).json()["code"]

        assert novo != antigo

    def test_o_codigo_no_login_atribui(self, client, monkeypatch):
        """A atribuição só acontece aqui — não há rota para aplicar depois."""
        _fingir_google(monkeypatch, "u_ref_login_novo")
        codigo = referral_service.code_for("u_ref_login_dono")

        resposta = client.post(
            "/api/auth/google", json={"id_token": "qualquer", "referral_code": codigo}
        )

        assert resposta.status_code == 200
        assert referral_service.status("u_ref_login_dono")["attributed"] == 1

    def test_codigo_ruim_no_login_nao_derruba_o_login(self, client, monkeypatch):
        """Perder a conta por causa de um brinde seria a troca errada: quem
        digitou um código errado ainda assim quer entrar."""
        _fingir_google(monkeypatch, "u_ref_login_ruim")

        resposta = client.post(
            "/api/auth/google", json={"id_token": "qualquer", "referral_code": "ZZZZZZZZ"}
        )

        assert resposta.status_code == 200
        assert resposta.json()["user"]["id"] == "u_ref_login_ruim"


class TestPrestacaoDeContas:
    def test_pendente_e_a_diferenca_entre_atribuido_e_qualificado(self, client):
        """É a informação útil: quem clicou mas ainda não montou carteira."""
        codigo = referral_service.code_for("u_ref_funil")
        referral_service.attribute("u_ref_funil_a", codigo)
        referral_service.attribute("u_ref_funil_b", codigo)
        salvar_posicao(client, "u_ref_funil_a")

        estado = referral_service.status("u_ref_funil")

        assert (estado["attributed"], estado["qualified"], estado["pending"]) == (2, 1, 1)
