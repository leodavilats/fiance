# ADR-022 — Dados de mercado coletados em lote, por um job dono do próprio schema

**Status:** PROPOSTO
**Data:** 2026-10-09
**Decidido por:** autor do projeto; as escolhas abertas estão declaradas aqui

## Contexto

A BRAPI é a única fonte de mercado, buscada sob demanda: quando alguém pede e o cache venceu. Toda
atualização traz o pacote inteiro — cotação, histórico, proventos e três módulos de balanço
(`backend/app/collectors/universal.py`) —, a varredura do universo reconsulta cerca de 280 ativos a
cada 30 minutos de pregão, e o custo cresce com o uso. A assinatura paga não foi feita.

O autor quer usar a **mesma base** para o aplicativo e para uma frente nova, de uso próprio: pesquisa
de estratégia de carteira em horizonte de meses. Essa frente precisa do que a BRAPI não entrega:
histórico longo, empresas que saíram da bolsa e fundamento como se sabia na data (*point-in-time*) —
a mesma lacuna que deixou a calibração do preço justo em [09-FUTURO](../09-FUTURO.md), *Considerado*.

## Problema

O invariante "só BRAPI e BCB SGS" amarra o sistema a um fornecedor cujo custo é variável e cujo dado
não serve para pesquisa. O disjuntor protege contra queda, não contra preço nem descontinuação.

## Alternativas

1. **Manter a BRAPI e reduzir o consumo** (varrer menos, tirar BDR e ETF da varredura, separar preço
   de fundamento). Rejeitada como solução: o custo cai, a dependência e a falta de histórico ficam.
2. **Trocar por outra API paga com cobertura da B3.** Rejeitada: a mesma dependência, com outro nome.
3. **Raspar sites de terceiros.** Rejeitada: fere termos de uso e quebra sem aviso.
4. **Coletar em lote, de fontes oficiais e gratuitas, num schema próprio.**

## Decisão

A alternativa 4. Um serviço novo, `data-job/`, baixa, interpreta e grava os dados de mercado no
schema `mercado` do Postgres. Quem consome — `backend/` e a pesquisa — só lê.

**Fontes:** B3 (COTAHIST), CVM dados abertos (DFP, ITR, FCA, informe mensal de FII) e BCB SGS. A BRAPI
continua no `backend/` até ele passar a ler do schema `mercado`, e só sai de vez quando proventos e
eventos de ações tiverem fonte decidida — a peça sem fonte oficial estruturada.

**Regras do data-job:**

- **Só ele escreve em `mercado`.** Consumidores usam um usuário de banco somente leitura.
- **O arquivo bruto é guardado antes de interpretar.** Reprocessar não exige baixar de novo, e todo
  número tem origem rastreável.
- **Rodar duas vezes dá o mesmo resultado.** Gravação por chave natural; arquivo de hash conhecido é
  pulado.
- **Fundamento nunca é sobrescrito.** Cada versão entregue à CVM é uma linha, com a data de entrega.
- **Preço bruto e evento corporativo são guardados separados.** O ajustado é derivado dos dois.
- **A identidade é o ISIN e o CNPJ, não o ticker.** O ticker é atributo com vigência.
- **Dado implausível vai para quarentena com o motivo**, não para o lixo nem para a tabela.
- **Toda execução deixa registro** (fonte, arquivo, hash, linhas, status).
- **Falha não apaga o que existe.** "O sistema não inventa dado" continua valendo.

**Onde mora, decidido em 2026-10-09 depois de medir:**

- **Um Postgres só do data-job** (serviço `postgres-mercado` no Railway, volume de 5 GB), e não o do
  aplicativo. Um ano de cotação ocupa 65 MB, e o volume do aplicativo tem 500 MB: o histórico não
  cabia, e disco cheio derruba o aplicativo. A proposta original era o mesmo banco.
- **Arquivos brutos num volume** montado no serviço do data-job (`/bruto`), e não num bucket: o
  armazenamento já é um diretório, e o volume não pede código novo.

**Enquanto esta ADR for `PROPOSTO`, o invariante de [CLAUDE.md](../../CLAUDE.md) vale.** Ao aceitá-la,
mudam no mesmo commit: o invariante "Fontes" de `CLAUDE.md`, a seção *Dados externos* de
[03-ARQUITETURA](../03-ARQUITETURA.md) e o item de calibração de [09-FUTURO](../09-FUTURO.md).

## Consequências

**Ganhos**

- O custo de fonte deixa de crescer com o uso: é número de arquivos por dia, e é zero
- Histórico de 20 anos, com as empresas que saíram da bolsa
- Fundamento com data de entrega, que destrava a calibração e a pesquisa
- Trocar uma fonte é trocar um coletor; quem consome não sabe de onde o dado veio

**Custos aceitos**

- **A cotação do aplicativo passa a ser a do último fechamento**, quando o `backend/` migrar. A idade
  continua visível pelo `formatAge`
- **A versão anterior de um balanço reapresentado se perde no histórico.** O índice da DFP lista todas
  as versões com a data de entrega; os arquivos de demonstração trazem só os números da mais recente.
  Do primeiro download em diante, o bruto guardado preserva cada versão
- **Proventos e eventos de ações não têm fonte oficial estruturada.** A fase 2 do plano decide
- Mais um serviço para operar, e parser de layout fixo para manter

## Referências

- Plano: [planos/data-job](../planos/data-job.md)
- `backend/app/collectors/universal.py` · `backend/app/core/universe.py` ·
  `backend/app/collectors/plausibility.py`
- B3, séries históricas: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/series-historicas/
- CVM, dados abertos: https://dados.cvm.gov.br/
