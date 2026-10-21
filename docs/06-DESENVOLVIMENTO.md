# Desenvolvimento

Como trabalhar no código de qualquer parte sem quebrar nada. O CI (`.github/workflows/ci.yml`) é a
fonte de verdade dos comandos; aqui está a explicação. O que é só do app está em
[app/desenvolvimento](app/desenvolvimento.md).
Última revisão: 2026-10-21

---

## Pronto = suíte verde

Tudo abaixo roda no CI a cada push. **Esta é a lista do CI, não um subconjunto dela.**

```bash
cd backend && python -m pytest -q
cd backend && python -m ruff check app tests migrations
cd backend && python -m ruff format --check app tests
cd data-job && python -m pytest -q                 # gravação exige DATAJOB_TEST_DATABASE_URL
cd data-job && python -m ruff check datajob tests migrations
cd data-job && python -m ruff format --check datajob tests migrations
cd fiance-dados && python -m pytest -q                # exige DADOS_API_TEST_DATABASE_URL e ../data-job/requirements.txt
cd fiance-dados && python -m ruff check dadosapi tests migrations
cd fiance-dados && python -m ruff format --check dadosapi tests migrations
cd fiance-trend/backend && python -m pytest -q            # exige ../../backend/requirements.txt instalado
cd fiance-trend/backend && python -m ruff check pesquisa api tests
cd fiance-trend/backend && python -m ruff format --check pesquisa api tests
cd fiance-trend/frontend && npm ci && npm run build && npm test
cd mobile  && flutter analyze && flutter test
cd mobile  && flutter build apk --release
python marca/build.py --check                      # requer Pillow
node docs/checar-links.mjs                         # job `documentacao`
```

**A suíte do `fiance-trend/backend` precisa das dependências do backend.** A calibração do preço justo
importa `app.*` do `backend/`; o CI instala `-r requirements.txt -r ../../backend/requirements.txt`.

### Uma ressalva que já custou tempo

**O `ruff format --check` já esteve fora daqui e dentro do CI.** Quem seguia o contrato à risca não
rodava o comando que reprovava, e o HEAD ficou vermelho sem ninguém ver. Se um comando está no CI,
está aqui.

---

## Ao adicionar…

| O quê | Faça também | Senão |
|---|---|---|
| Campo calculado numa resposta | Declarar no modelo Pydantic **e** no `fromJson` do Dart | Some **em silêncio** |
| Limiar de score | Mudar nas duas plataformas, **Python primeiro** | Réguas divergem |
| Coluna ou tabela num banco | Migração Alembic **da parte dona do schema**: `backend/migrations/`, `data-job/migrations/` ou `fiance-dados/migrations/` | O teste de migração da parte falha, ou o deploy sobe sem a coluna |
| Visão nova em `mercado` | `GRANT SELECT` para `mercado_leitura` na mesma migração do data-job, como as migrações de visão já fazem | A API e o painel recebem erro de permissão |
| Rota nova na API de dados | Recurso do plano, se for paga, e a linha em [dados/](dados/README.md) | Plano promete o que não entrega, ou entrega de graça |
| Estudo novo no laboratório | Protocolo em [pesquisa/estudos/](pesquisa/estudos/), aceito **antes** do código rodar | O resultado não vale como medida |
| Documento que o painel deve mostrar | Entrar em `fiance-trend/backend/api/arquivos.py` | O painel não o lista |

O resto da tabela, só do app, está em [app/desenvolvimento](app/desenvolvimento.md).

---

## Armadilhas que não quebram o build

Cada item já quebrou a tela ou o dado **com o CI verde**.

**Construtor que ignora chave não declarada.** `Modelo(**resultado.__dict__)` no Pydantic e o
`fromJson` no Dart descartam campo não declarado sem avisar. Três campos calculados nunca chegaram ao
cliente assim: `consensus_methods`, `trend_basis`, `allocation_gaps`.

**Campo obrigatório novo no Dart quebra quem não atualizou.** O cliente chega por loja: há versão
antiga instalada por tempo indeterminado, e ela não se atualiza no próximo carregamento. Campo novo
nasce opcional.

**Vocabulário sem consumidor** é pior que vocabulário nenhum — parece resolvido enquanto quatro telas
reescrevem o mapa à mão.

**Série nova no vocabulário sem entrar nos mapas de classe.** Uma categoria em `series: 4` pedia a
classe da série 4 e recebia nada, porque os mapas eram montados só das séries de alocação.

**Regra de lint que filtra por extensão de arquivo não roda.** Confira contra o que o repositório
tem, não contra o que a extensão sugere.

---

## Comentários: quase nunca

**O porquê vive nas [decisões](decisoes/); o que não pode ser violado vive no `CLAUDE.md`.** O fonte
não é lugar de nenhum dos dois — comentário de justificativa envelhece calado, não é lido por quem
mais precisa, e duplica o que já está escrito em lugar melhor.

**Não entra no código:**

- narrativa histórica: "isto era X e virou Y"
- justificativa de decisão que já está numa ADR
- comentário que repete o que a linha faz, incluindo docstring que reescreve a assinatura
- explicação de teste em docstring — a razão de um teste existir vai na **mensagem do assert**, que é
  onde ela aparece quando ele falha

**Fica:**

| Onde | Por quê |
|---|---|
| Infra — CI, migração, gerador, build, script de operação | Não tem ADR própria, e quem lê está prestes a executar |
| Armadilha local, em uma linha | O comentário evita o defeito ali, e ele não é óbvio na linha seguinte |
| Escape declarado que uma regra de lint exige | `// design-exception: regra — motivo` é contrato com a máquina |

Se a explicação é boa demais para caber em uma linha, ela não é comentário: é uma ADR.

---

## Testes

| Suíte | O que cobre |
|---|---|
| `backend/tests` | Domínio, API, contrato de rotas, arquitetura, dinheiro, privacidade |
| `mobile/test/lint_ui_test.dart` | 17 regras de produto |
| `mobile/test/contraste_test.dart` | WCAG nos dois temas |
| `mobile/test/jornada_do_app_test.dart` | Ponta a ponta do app com o roteador e as telas reais e a API simulada: os cinco destinos abrem sem quebrar, e as URLs antigas continuam chegando |
| `mobile/test/alvo_de_toque_test.dart` | Alvo de toque de 44dp e ação de toque na semântica dos componentes de toque |
| `mobile/test/fonte_grande_test.dart` | Toda tela com conteúdo cabe em 320dp com a letra quadrada do teste, que tem a largura da fonte do sistema em cerca de 200% |
| `mobile/test` | Widgets e modelos |
| `data-job/tests` | Leitura de cada fonte (COTAHIST, CVM, B3, BCB, Tesouro), rotina diária e gravação. A gravação roda contra um Postgres descartável em `DATAJOB_TEST_DATABASE_URL` — ela **apaga o schema `mercado`** desse banco; sem a variável, esses testes são pulados |
| `fiance-dados/tests` | Acesso (chave, limites, situação da conta), cobrança e as rotas de dado, contra um Postgres descartável em `DADOS_API_TEST_DATABASE_URL`, com as migrações do data-job aplicadas |
| `fiance-trend/backend/tests` | API do painel, alertas de coleta, motor, fundamentos, ranking, calibração, os estudos de 2026-10-19 e a validação contra a brapi |
| `fiance-trend/frontend` (`npm test`, Vitest) | Formatação, links entre documentos e série do gráfico |

**A razão de um teste existir vai na mensagem do assert.** É onde ela aparece quando ele falha.

---

## Convenções

- Python 3.13, ruff para lint e formatação
- Nomes de domínio em português quando o domínio é brasileiro (`apuracao`, `cascata`, `sobra`)
- `StrEnum` para vocabulário fechado, e o tipo recusa valor fora dele
- Dataclass congelada para resultado de cálculo
- Erro de domínio herda de `DomainError` e carrega `status_code`
