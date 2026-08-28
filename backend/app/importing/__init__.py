"""Importação de operações: colar lista ou subir CSV.

Módulo puro — recebe texto, devolve lançamentos e problemas. Não conhece banco
nem usuário, pelo mesmo motivo que `app/ledger` não conhece: dá para testar cada
formato malformado sem subir nada.

Duas regras vêm do critério de aceite e são o motivo do desenho:

* **Erro diz a linha e o que corrigir.** "Formato inválido" não ajuda ninguém a
  consertar um arquivo de trezentas linhas.
* **Duplicidade é apresentada para decisão, nunca silenciada.** Importar a mesma
  nota duas vezes é o erro mais comum, e resolvê-lo escondendo a segunda cópia
  faz o usuário perder uma operação legítima que por acaso era idêntica.
"""

from .parser import (
    ImportIssue,
    ImportRow,
    ParsedImport,
    parse_import,
)

__all__ = [
    "ImportIssue",
    "ImportRow",
    "ParsedImport",
    "parse_import",
]
