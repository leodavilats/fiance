# ADR-001 — Matemática pura separada da persistência

**Status:** ACEITO
**Data:** 2026-09-13 *(adoção retroativa de um padrão já vigente)*
**Decidido por:** autor do projeto

## Contexto

`ledger/`, `cashflow/` e `analysis/` não importam nada de banco de dados. Recebem dados por
parâmetro e devolvem resultados. Quem liga isso à persistência são os `*_service.py`.

Esse padrão **surgiu do código gerado por IA, não de uma decisão deliberada**. Foi identificado
durante a reconstrução da documentação em 2026-09-13, quando se perguntou por que as camadas estavam
assim — e a resposta honesta era "não sei, veio assim".

## Problema

Um padrão que ninguém decidiu não é invariante: é coincidência. A próxima sessão de trabalho, humana
ou de IA, não tem razão para respeitá-lo, e a primeira consulta ao banco dentro de `analysis/`
passaria despercebida em revisão.

A pergunta a responder era: **isto é bom o suficiente para virar regra, ou é só o jeito que saiu?**

## Alternativas

1. **Adotar formalmente** — vira invariante, com teste de arquitetura para sustentá-lo
2. **Manter sem se comprometer** — continua sendo hábito, e erode
3. **Reorganizar** para um padrão convencional de serviço com acesso a dados

## Decisão

**Adotar formalmente.** A separação vira invariante documentado.

A razão é medível: existem cerca de 13 mil linhas de teste no backend, e elas só são baratas porque a
matemática não precisa de banco para rodar. Um teste de apuração de imposto não sobe Postgres, não
semeia tabela, não limpa estado. Um bug de cálculo é um bug localizável em função pura.

A alternativa 3 foi descartada sem hesitação: trocaria uma propriedade valiosa por familiaridade.

## Consequências

**Ganhos**

- A matemática financeira é testável sem infraestrutura
- Um erro de regra de negócio é localizável em função pura, não em efeito de consulta
- O cálculo **não pode** saber quem paga, o que sustenta o isolamento da monetização
  ([ADR-008](ADR-008-monetizacao-por-loja.md)) — dois testes de arquitetura travam isso

**Custos aceitos**

- Dado que o cálculo precisa tem de ser buscado antes e passado por parâmetro, o que às vezes
  significa buscar mais do que se usa
- A camada de serviço fica mais gorda: ela carrega a orquestração inteira
- Há uma indireção a mais entre a rota e o resultado

**A regra prática:** se um módulo de `ledger/`, `cashflow/` ou `analysis/` precisar importar
`storage/` ou `models/db_*`, a solução está errada. Passe o dado por parâmetro.

## Referências

- [03-ARQUITETURA](../03-ARQUITETURA.md)
- `backend/app/ledger/`, `backend/app/cashflow/`, `backend/app/analysis/`
- Testes de arquitetura em `backend/tests/`
