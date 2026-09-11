"""O que o removedor não pode confundir com comentário.

Rodar: `python -m pytest tool/test_remover_comentarios.py -q`
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from remover_comentarios import limpar_dart, limpar_python  # noqa: E402


def dart(fonte, tudo=False):
    return limpar_dart(fonte, tudo)[0]


def py(fonte, tudo=False, docstrings=False):
    return limpar_python(fonte, tudo, docstrings)[0]


class TestDartNaoApagaTexto:
    def test_barra_dupla_dentro_de_string_fica(self):
        fonte = "const url = 'https://fiance.app/termos';"
        assert dart(fonte) == fonte

    def test_barra_dupla_em_string_crua_fica(self):
        fonte = r"final re = RegExp(r'//+\s*ignore');"
        assert dart(fonte) == fonte

    def test_interpolacao_com_aspas_dentro_nao_abre_comentario(self):
        fonte = "final s = 'a ${m['k']} b'; // some"
        assert dart(fonte).strip() == "final s = 'a ${m['k']} b';"

    def test_aspas_escapada_nao_fecha_a_string(self):
        fonte = r"""final s = 'não \' acabou // aqui'; // some"""
        assert dart(fonte).strip() == r"""final s = 'não \' acabou // aqui';"""

    def test_string_tripla_atravessa_linha(self):
        fonte = "final s = '''\nlinha // não é comentário\n''';\n// some\n"
        saida = dart(fonte)
        assert "// não é comentário" in saida
        assert "// some" not in saida


class TestDartRemove:
    def test_comentario_de_linha_inteira_leva_a_linha(self):
        fonte = "final a = 1;\n// nota\nfinal b = 2;\n"
        assert dart(fonte) == "final a = 1;\nfinal b = 2;\n"

    def test_comentario_no_fim_da_linha_deixa_o_codigo(self):
        assert dart("final a = 1; // nota\n") == "final a = 1;\n"

    def test_doc_comment_sai(self):
        fonte = "/// A régua.\nclass FiMeasure {}\n"
        assert dart(fonte) == "class FiMeasure {}\n"

    def test_bloco_aninhado_sai_inteiro(self):
        fonte = "final a = 1;\n/* fora /* dentro */ ainda fora */\nfinal b = 2;\n"
        saida = dart(fonte)
        assert "fora" not in saida and "dentro" not in saida
        assert "final a = 1;" in saida and "final b = 2;" in saida


class TestDartPreservaDiretiva:
    def test_ignore_fica(self):
        fonte = "// ignore: deprecated_member_use\nfinal a = 1;\n"
        assert dart(fonte) == fonte

    def test_design_exception_fica(self):
        fonte = "// design-exception: explicabilidade — o erro não é julgamento\nfinal a = 1;\n"
        assert dart(fonte) == fonte

    def test_com_tudo_a_diretiva_sai(self):
        fonte = "// ignore: deprecated_member_use\nfinal a = 1;\n"
        assert dart(fonte, tudo=True) == "final a = 1;\n"


class TestPythonNaoApagaTexto:
    def test_cerquilha_dentro_de_string_fica(self):
        fonte = 'url = "https://x/#ancora"\n'
        assert py(fonte) == fonte

    def test_cerquilha_em_string_tripla_fica(self):
        fonte = 's = """\n# não é comentário\n"""\n'
        assert py(fonte) == fonte


class TestPythonRemove:
    def test_linha_inteira_sai(self):
        assert py("a = 1\n# nota\nb = 2\n") == "a = 1\nb = 2\n"

    def test_fim_de_linha_deixa_o_codigo(self):
        assert py("a = 1  # nota\n") == "a = 1\n"


class TestPythonPreservaDiretiva:
    def test_noqa_fica(self):
        fonte = "import redis  # noqa: PLC0415\n"
        assert py(fonte) == fonte

    def test_pragma_fica(self):
        fonte = "except Exception:  # pragma: no cover\n    pass\n"
        assert py(fonte) == fonte

    def test_shebang_fica(self):
        fonte = "#!/usr/bin/env python3\na = 1\n"
        assert py(fonte) == fonte

    def test_com_tudo_o_noqa_sai(self):
        assert py("import redis  # noqa: PLC0415\n", tudo=True) == "import redis\n"


class TestDocstring:
    def test_por_padrao_a_docstring_fica(self):
        fonte = '"""Módulo."""\n\na = 1\n'
        assert py(fonte) == fonte

    def test_com_a_opcao_ela_sai(self):
        fonte = '"""Módulo."""\n\na = 1\n'
        assert "Módulo" not in py(fonte, docstrings=True)

    def test_docstring_que_e_o_corpo_inteiro_nao_sai(self):
        fonte = 'def f():\n    """Só isto."""\n'
        assert py(fonte, docstrings=True) == fonte, (
            "remover deixaria a função sem corpo, e o arquivo não compilaria"
        )
