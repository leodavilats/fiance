from __future__ import annotations

import pathlib
import re

import pytest

from app.analysis import score_ruler

_PRODUCT_RULES = (
    pathlib.Path(__file__).resolve().parents[2] / "mobile" / "lib" / "core" / "product_rules.dart"
)

_LIMIARES = (
    ("kScoreStrong", score_ruler.SCORE_STRONG),
    ("kScoreGood", score_ruler.SCORE_GOOD),
    ("kScoreNeutral", score_ruler.SCORE_NEUTRAL),
    ("kHighlightMinDy", score_ruler.HIGHLIGHT_MIN_DY),
    ("kMinDataCompleteness", score_ruler.MIN_DATA_COMPLETENESS),
)


def _valor_no_dart(fonte: str, nome: str) -> float | None:
    achado = re.search(rf"const\s+double\s+{nome}\s*=\s*([0-9.]+)\s*;", fonte)
    return float(achado.group(1)) if achado else None


@pytest.mark.skipif(not _PRODUCT_RULES.exists(), reason="repositório sem a pasta mobile")
@pytest.mark.parametrize(("nome", "esperado"), _LIMIARES)
def test_o_dart_usa_o_mesmo_limiar_do_python(nome: str, esperado: float):
    dart = _valor_no_dart(_PRODUCT_RULES.read_text(encoding="utf-8"), nome)

    assert dart is not None, (
        f"{nome} sumiu de product_rules.dart. A régua de score vive nas duas plataformas e "
        "este teste é a única coisa que as compara."
    )

    assert dart == esperado, (
        f"{nome}: Python diz {esperado}, Dart diz {dart}. O Python é a fonte — mude lá "
        "primeiro e espelhe aqui, senão a tela classifica um número que o servidor "
        "classificou de outro jeito."
    )


def test_score_confiavel_respeita_o_piso():
    assert score_ruler.score_confiavel(None) is True, (
        "sem informação de completude, o score é tratado como completo — é o que o Dart faz "
        "com o default de 1."
    )
    assert score_ruler.score_confiavel(1.0) is True
    assert score_ruler.score_confiavel(score_ruler.MIN_DATA_COMPLETENESS) is True
    assert score_ruler.score_confiavel(0.35) is False, (
        "0.35 é a completude de uma ação sem roe, margem e crescimento no perfil arrojado — "
        "o caso que o piso existe para marcar."
    )


_VOCABULARY = (
    pathlib.Path(__file__).resolve().parents[2] / "mobile" / "lib" / "core" / "vocabulary.dart"
)


@pytest.mark.skipif(not _VOCABULARY.exists(), reason="repositório sem a pasta mobile")
def test_todo_tipo_de_lancamento_tem_rotulo_no_dart():
    from app.ledger import TransactionKind

    fonte = _VOCABULARY.read_text(encoding="utf-8")
    bloco = re.search(r"const Map<String, String> fiLedgerKinds = \{(.*?)\};", fonte, re.DOTALL)
    assert bloco, "fiLedgerKinds sumiu de vocabulary.dart."

    declarados = set(re.findall(r"'([a-z_]+)':", bloco.group(1)))
    faltando = sorted({k.value for k in TransactionKind} - declarados)

    assert faltando == [], (
        f"tipo de lançamento sem rótulo no Dart: {faltando}. A tela do razão mostraria o "
        "código cru — 'transfer_in' no lugar de 'Transferência de entrada'."
    )


@pytest.mark.skipif(not _VOCABULARY.exists(), reason="repositório sem a pasta mobile")
def test_o_rotulo_de_categoria_e_o_mesmo_nas_duas_plataformas():
    from app.services.dashboard_service import _CATEGORY_LABELS

    fonte = _VOCABULARY.read_text(encoding="utf-8")
    bloco = re.search(r"const Map<String, FiCategory> fiCategories = \{(.*?)\};", fonte, re.DOTALL)
    assert bloco, "fiCategories sumiu de vocabulary.dart."

    no_dart = dict(re.findall(r"'([a-z_]+)':\s*FiCategory\('([^']+)'", bloco.group(1)))
    divergentes = {
        chave: (rotulo, no_dart.get(chave))
        for chave, rotulo in _CATEGORY_LABELS.items()
        if no_dart.get(chave) != rotulo
    }

    assert divergentes == {}, (
        f"categoria com rótulo diferente entre servidor e app: {divergentes}. O painel vem com o "
        "rótulo do servidor e a carteira com o do app: a mesma categoria apareceria com dois nomes."
    )
