from __future__ import annotations

import pytest

from app.core.telemetry import configurar_sentry, limpar_caminho, limpar_evento, limpar_texto


class TestOCaminhoNaoEntregaOPapel:
    def test_ticker_no_caminho_vira_marcador(self):
        assert limpar_caminho("/api/v1/asset/PETR4") == "/api/v1/asset/{id}"
        assert limpar_caminho("/api/v1/asset/HGLG11/history") == "/api/v1/asset/{id}/history"

    def test_id_numerico_e_uuid_tambem(self):
        assert limpar_caminho("/api/fixed-income/4821") == "/api/fixed-income/{id}"
        assert limpar_caminho("/api/transactions/0f9c1a2b3d4e5f60") == "/api/transactions/{id}"

    def test_a_rota_continua_reconhecivel(self):
        assert limpar_caminho("/api/v1/portfolio/trades") == "/api/v1/portfolio/trades"

    def test_url_absoluta_mantem_host(self):
        assert (
            limpar_caminho("https://fiance.up.railway.app/api/asset/VALE3")
            == "https://fiance.up.railway.app/api/asset/{id}"
        )

    def test_a_query_nao_atravessa(self):
        assert limpar_caminho("/api/opportunities?q=PETR&token=abc") == "/api/opportunities"


class TestOTextoNaoEntregaOValor:
    def test_valor_em_reais_e_redigido(self):
        assert "38" not in limpar_texto("Venda de PETR4 com lucro de R$ 38.400,00")

    def test_quantidade_citada_em_erro_de_validacao_e_redigida(self):
        limpo = limpar_texto("Quantidade de venda (300) maior que a quantidade em carteira (100).")

        assert "300" not in limpo
        assert "100" not in limpo
        assert "Quantidade de venda" in limpo, "a causa do erro continua legível"

    def test_segredo_em_url_continua_redigido(self):
        assert "[redigido]" in limpar_texto("GET https://brapi.dev/api/quote?token=segredo123")
        assert "segredo123" not in limpar_texto("GET https://brapi.dev/api/quote?token=segredo123")


class TestOEventoInteiro:
    @pytest.fixture()
    def evento(self) -> dict:
        return {
            "message": "falhou ao vender R$ 12.500,00",
            "request": {
                "method": "POST",
                "url": "https://fiance.up.railway.app/api/portfolio/sell/PETR4",
                "query_string": "token=segredo",
                "cookies": {"session": "abc"},
                "data": {"ticker": "PETR4", "quantity": 300, "avg_price": 38.4},
                "headers": {
                    "X-Request-Id": "req-1",
                    "Authorization": "Bearer segredo",
                    "Cookie": "session=abc",
                },
            },
            "user": {"id": "u_123", "email": "alguem@exemplo.com", "username": "Alguém"},
            "extra": {"posicao": {"ticker": "PETR4", "avg_price": 38.4}},
            "breadcrumbs": {
                "values": [
                    {
                        "message": "GET /api/asset/PETR4",
                        "data": {"quantity": 300, "avg_price": 38.4},
                    }
                ]
            },
            "exception": {
                "values": [
                    {
                        "type": "DomainError",
                        "value": "Quantidade de venda (300) maior que a carteira (100).",
                        "stacktrace": {
                            "frames": [
                                {
                                    "function": "sell_position",
                                    "vars": {"avg_price": "38.4", "quantity": "300"},
                                }
                            ]
                        },
                    }
                ]
            },
        }

    def test_o_corpo_do_request_nao_sai(self, evento):
        limpo = limpar_evento(evento)

        assert "data" not in limpo["request"]
        assert "cookies" not in limpo["request"]
        assert "query_string" not in limpo["request"]

    def test_so_cabecalho_da_lista_de_permissao_sai(self, evento):
        cabecalhos = limpar_evento(evento)["request"]["headers"]

        assert set(cabecalhos) == {"X-Request-Id"}

    def test_do_usuario_sai_o_identificador_e_mais_nada(self, evento):
        assert limpar_evento(evento)["user"] == {"id": "u_123"}

    def test_contexto_solto_e_variavel_de_frame_nao_saem(self, evento):
        limpo = limpar_evento(evento)

        assert "extra" not in limpo
        frame = limpo["exception"]["values"][0]["stacktrace"]["frames"][0]
        assert "vars" not in frame
        assert frame["function"] == "sell_position", "onde quebrou continua ali"

    def test_o_dado_do_breadcrumb_nao_sai_e_o_ticker_some_do_texto(self, evento):
        trilha = limpar_evento(evento)["breadcrumbs"]["values"][0]

        assert "data" not in trilha

    def test_nenhum_valor_da_carteira_sobrevive_no_evento_serializado(self, evento):
        import json

        texto = json.dumps(limpar_evento(evento), ensure_ascii=False)

        for vazamento in ["38.4", "12.500", "alguem@exemplo.com", "segredo"]:
            assert vazamento not in texto, f"{vazamento!r} chegaria ao Sentry"


class TestLigarEDesligar:
    def test_sem_dsn_nao_liga_e_nao_reclama(self, monkeypatch):
        from app.core import config

        monkeypatch.setattr(config.get_settings(), "sentry_dsn", "", raising=False)

        assert configurar_sentry() is False

    def test_dsn_configurado_sem_o_pacote_falha_alto(self, monkeypatch):
        import builtins

        from app.core import config
        from app.core.telemetry import SentryNaoInstalado

        monkeypatch.setattr(
            config.get_settings(), "sentry_dsn", "https://exemplo@sentry.io/1", raising=False
        )

        importar = builtins.__import__

        def sem_sentry(nome, *args, **kwargs):
            if nome.startswith("sentry_sdk"):
                raise ImportError(nome)
            return importar(nome, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", sem_sentry)

        with pytest.raises(SentryNaoInstalado):
            configurar_sentry()
