# Arquitetura

Como as partes do fiance se ligam, quem escreve e quem lê cada dado, e por que as fronteiras estão
onde estão. Por dentro de cada parte: [app/arquitetura](app/arquitetura.md),
[base/](base/README.md), [dados/](dados/README.md), [pesquisa/](pesquisa/README.md).
Última revisão: 2026-10-21

---

## Visão geral

Quatro serviços e dois Postgres, no mesmo projeto do Railway, sem fila.

```
                fontes oficiais: B3, CVM, BCB, Tesouro
                                 │ HTTP, uma vez por dia útil
                         ┌───────▼────────┐
                         │  data-job/     │  cron 23h de Brasília; bruto no volume /bruto
                         └───────┬────────┘
                                 │ escreve só `mercado`
                    ┌────────────▼──────────────┐
                    │  postgres-mercado         │
                    │  schemas mercado + acesso │
                    └─────▲───────────────▲─────┘
       lê `mercado` como  │               │ lê `mercado` como
       mercado_leitura;   │               │ mercado_leitura
       escreve `acesso`   │               │
                 ┌────────┴───────┐  ┌────┴───────────┐
  terceiros ────►│ fiance-dados/  │  │ fiance-trend/  │◄── o autor, com senha
  por chave      │ API de dados   │  │ laboratório    │
                 └────────▲───────┘  └────────────────┘
                          │ HTTP na rede privada, chave do plano `interno`
                 ┌────────┴───────┐       ┌──────────────┐
                 │ backend/       │◄─────►│ postgres-app │
                 │ FastAPI        │       └──────────────┘
                 └────────▲───────┘
                          │ HTTPS /api/v1
                 ┌────────┴───────┐
                 │ mobile/        │  o único cliente do app
                 └────────────────┘
```

## Quem escreve, quem lê

| Dado | Escreve | Lê |
|---|---|---|
| Schema `mercado` (`postgres-mercado`) | Só o `data-job/` | `fiance-dados/` e `fiance-trend/`, como `mercado_leitura`, em transação só de leitura |
| Schema `acesso` (`postgres-mercado`) | Só a `fiance-dados/` | Só a `fiance-dados/` |
| `postgres-app` | Só o `backend/` | Só o `backend/` |
| Registros e resultados da pesquisa | `fiance-trend/backend/pesquisa/`, à mão, e versionados | O painel |

**O backend do app não abre o banco de mercado.** Ele é cliente da API de dados, com uma chave do
plano `interno` e os mesmos limites que um terceiro teria
([ADR-024](decisoes/ADR-024-api-de-dados.md)). O que a API não entrega, o app não tem.

**O laboratório lê o banco direto**, sem passar pela API: precisa de todas as tabelas e visões, e
não é produto ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)). Ele importa o motor de cálculo
do backend (`app.analysis`) para medir o mesmo veredito que o app mostra.

**O papel `mercado_leitura`** não tem login nem senha: os leitores usam a conexão que o Railway dá
ao `postgres-mercado` e o assumem com `SET ROLE` a cada conexão aberta. Ele é criado e mantido pelas
migrações do data-job.

## Fronteiras que não se negociam

- **Só o `data-job/` escreve dado de mercado**, e só a partir de fonte oficial, com o bruto guardado
  antes de interpretar ([ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md)). Nenhuma
  outra parte coleta.
- **Regra de negócio do app vive só no backend** (`analysis/`, `ledger/`, `cashflow/`), que não
  conhece banco ([ADR-001](decisoes/ADR-001-matematica-pura.md)). O cliente Flutter delega.
- **Cada serviço que tem banco tem as suas migrações**, e nenhum migra o schema de outro:
  `backend/migrations/`, `data-job/migrations/` (schema `mercado`), `fiance-dados/migrations/`
  (schema `acesso`).
- **O `cvm_estimado` não sai do laboratório.** O rendimento de FII estimado pela CVM é dado de
  pesquisa: a API não o entrega por padrão, e o app nunca o pede.

## O sistema não inventa dado

Vale em todas as partes, e cada uma o aplica no seu ponto:

| Parte | Como |
|---|---|
| Base | Linha implausível vai para a quarentena; evento sem prova primária não ajusta a série, e o salto fica marcado |
| API de dados | Ticker que a base não tem é 404; a idade de cada dado sai em `/v1/atualidade` |
| App | Fonte fora do ar degrada em ordem: cache válido → cache vencido com idade visível → ausência declarada. **Falha de rede não vira ausência** ([app/arquitetura](app/arquitetura.md#dados-externos)) |
| Laboratório | Só o que se sabia em cada data entra na medida; o painel alerta a coleta parada |

## O ritmo do dado

O dado de mercado chega **em lote, uma vez por dia útil**: o `data-job` roda às 23h de Brasília,
depois de cada pregão, e proventos e eventos da B3 às sextas. Tudo o que vem depois — a API, o app,
o painel — serve o último fechamento, nunca o pregão em andamento. Por isso o app guarda o dado de
mercado até a próxima carga, e não por um prazo fixo: durante o dia, reler a base não traz nada novo.

## Operação

Serviços, variáveis, deploy e backup: [07-OPERACAO](07-OPERACAO.md).
