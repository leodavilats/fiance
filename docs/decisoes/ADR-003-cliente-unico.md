# ADR-003 — Flutter como cliente único; web descontinuada

**Status:** ACEITO
**Data:** 2026-09-11 · commit `3a922a6`

## Contexto

O produto tinha dois clientes sobre a mesma API: um front Angular com renderização no servidor, 191
testes, E2E de navegador, 24 regras de lint e uma landing page; e um aplicativo Flutter, mais novo e
ainda incompleto.

## Problema

Manter duas interfaces custava **cada tela duas vezes e cada regra de produto duas vezes**, e
transformava paridade em trabalho permanente.

E a paridade quebrava sempre no **conceito**, nunca na cor: uma tela ganhava um estado, uma régua
mudava de banda, um texto era reescrito — e a outra plataforma ficava para trás de um jeito que
nenhum teste pegava.

O público-alvo — assalariado sem tempo, consultando no celular — não pedia desktop. E a monetização
pretendida é por loja.

## Alternativas

1. **Manter as duas**, aceitando o custo permanente
2. **Só o aplicativo**, descontinuando a web
3. Só a web, descontinuando o aplicativo
4. Web reduzida a landing page e páginas jurídicas

A alternativa 3 foi descartada pela distribuição e pela monetização. A 4 foi parcialmente adotada: as
páginas jurídicas ficaram, a landing não.

## Decisão

**O front Angular sai inteiro do repositório.** O Flutter é o único cliente, distribuído pelas lojas.

O que o front carregava e não era tela foi realocado:

- **o texto jurídico passou para o backend** (`api/legal.py` + `services/legal_pages.py`), fora de
  `/api`. Não é conveniência: `legal_links.dart` já apontava para o domínio da API, então os três
  links de dentro do aplicativo estavam quebrados antes disto. As lojas exigem uma URL de privacidade
  que abra sem login
- **a landing saiu com o que a sustentava**: `POST /public/interest` e sua tabela,
  `GET /public/universe` e o gerador de og-image. Ficou `GET /public/asset/{ticker}`

## Consequências

**Ganhos**

- Cada tela e cada regra de produto existem uma vez só
- Paridade deixou de ser trabalho permanente
- As páginas jurídicas passaram a funcionar — antes estavam quebradas

**Custos aceitos**

- Não há acesso por navegador. Quem quiser ver a carteira no computador não tem como
- Saíram 191 testes, o E2E de navegador e 24 regras de lint. **Três dessas regras ainda não têm
  equivalente no Dart** — ver [10-PROBLEMAS](../10-PROBLEMAS.md), item 14
- Não há mais landing page, e portanto **nenhuma superfície pública de descoberta do produto**. Isso
  se agrava com a decisão de não ter gratuidade ([ADR-009](ADR-009-trial-e-gratuidade.md))

**Custo não previsto, e o maior de todos:** o aplicativo Flutter **não tinha paridade** no momento da
remoção. Nove funcionalidades ficaram sem cliente — entre elas o livro-razão, a importação de extrato
e a gestão de proventos. O backend continua servindo todas.

Ver [PARIDADE-WEB-APP](../temporario/PARIDADE-WEB-APP.md).

## Referências

- commit `3a922a6`, 2026-09-11
- [08-ESTADO](../08-ESTADO.md)
