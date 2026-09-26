from datetime import date, timedelta

from app.api.onboarding import STEP_GOALS
from tests.conftest import make_auth_headers


def test_carteira_so_de_renda_fixa_tambem_passa_do_passo_da_carteira(client):
    headers = make_auth_headers("u_onb_renda_fixa")
    hoje = date.today()
    client.post(
        "/api/v1/fixed-income",
        headers=headers,
        json={
            "nome": "CDB diário",
            "tipo": "cdb",
            "valor_investido": 5000.0,
            "taxa": 13.0,
            "tipo_taxa": "pre_fixado",
            "data_aplicacao": (hoje - timedelta(days=30)).isoformat(),
            "vencimento": (hoje + timedelta(days=365)).isoformat(),
            "liquidez": "diaria",
        },
    )

    corpo = client.get("/api/v1/onboarding", headers=headers).json()

    assert corpo["step"] == STEP_GOALS, (
        "'tem carteira' é has_holdings(), que olha posições e renda fixa: quem só tem CDB "
        "já registrou a carteira"
    )
