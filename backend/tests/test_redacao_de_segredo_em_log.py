import logging

import pytest

from app.core.observability import RedigeSegredoEmURL, instalar_redacao

URL_DA_BRAPI = (
    "HTTP Request: GET https://brapi.dev/api/quote/UNIP3"
    "?token=2GeD98554sLjKhM6D98kYs&fundamental=true&range=3mo "
    '"HTTP/1.1 200 OK"'
)


def _redigir(mensagem, *args):
    registro = logging.LogRecord(
        name="httpx",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=mensagem,
        args=args or None,
        exc_info=None,
    )
    RedigeSegredoEmURL().filter(registro)
    return registro.getMessage()


class TestOSegredoNaoChegaAoLog:
    def test_o_token_da_brapi_sai_da_url(self):
        saida = _redigir(URL_DA_BRAPI)

        assert "2GeD98554sLjKhM6D98kYs" not in saida
        assert "token=[redigido]" in saida

    def test_o_resto_da_url_sobrevive(self):
        saida = _redigir(URL_DA_BRAPI)

        assert "brapi.dev/api/quote/UNIP3" in saida
        assert "fundamental=true" in saida
        assert "200 OK" in saida

    @pytest.mark.parametrize(
        "parametro",
        ["token", "api_key", "apikey", "access_token", "refresh_token", "secret", "password"],
    )
    def test_cobre_os_nomes_usuais(self, parametro):
        saida = _redigir(f"GET https://exemplo/x?{parametro}=abc123&y=1")

        assert "abc123" not in saida
        assert "y=1" in saida

    def test_redige_tambem_quando_a_mensagem_e_interpolada(self):
        saida = _redigir("GET %s", "https://exemplo/x?token=abc123")

        assert "abc123" not in saida

    def test_nao_confunde_palavra_que_termina_em_token(self):
        saida = _redigir("csrftoken=abc123")

        assert saida == "csrftoken=abc123"


class TestAInstalacao:
    def test_poe_o_filtro_no_handler_e_cala_o_httpx(self):
        raiz = logging.getLogger()
        handler = logging.StreamHandler()
        raiz.addHandler(handler)
        nivel_original = logging.getLogger("httpx").level
        try:
            instalar_redacao()

            assert any(isinstance(f, RedigeSegredoEmURL) for f in handler.filters)
            assert logging.getLogger("httpx").level == logging.WARNING
        finally:
            raiz.removeHandler(handler)
            logging.getLogger("httpx").setLevel(nivel_original)

    def test_e_idempotente(self):
        raiz = logging.getLogger()
        handler = logging.StreamHandler()
        raiz.addHandler(handler)
        try:
            instalar_redacao()
            instalar_redacao()

            filtros = [f for f in handler.filters if isinstance(f, RedigeSegredoEmURL)]
            assert len(filtros) == 1
        finally:
            raiz.removeHandler(handler)
