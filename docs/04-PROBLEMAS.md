# Problemas conhecidos

**Fonte de verdade** do que está aberto, em todas as partes. Só pendências: nada de histórico, nada
de item resolvido — o que saiu está no git e nas [decisões](decisoes/).
Última verificação contra o código: **2026-10-21**

> **Ao fechar um item, apague-o daqui.** Item resolvido que fica é pior que item ausente, porque
> manda alguém refazer o que já existe. Este arquivo tem histórico de apodrecer: numa revisão de
> agosto, oito de 24 itens já estavam feitos.

Os números (21, 25, 26, 27) são de verificações antigas e ficam porque outros documentos os citam.
**Bloqueia só a fase pública** marca o que não pesa enquanto o uso é pessoal
([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)).

---

## Transversal

### Nenhum banco tem backup automático

Vale para os dois: `postgres-app` e `postgres-mercado`. **Risco aceito pelo autor em 2026-10-12**,
enquanto o uso é pessoal ([07-OPERACAO](07-OPERACAO.md#backup-e-recuperação)). A cópia lógica do
`postgres-app` e a restauração existem e são testadas (`backend/app/backup.py`), mas não são agendadas;
o `postgres-mercado` se reconstrói do bruto do data-job, menos o que as fontes já não publicam.
**Reabre antes de abrir qualquer produto ao público:** agendar a exportação, com destino cifrado e
retenção de no máximo 30 dias.

---

## App

### Duas rotas sem cliente

`GET /whats-new` (`backend/app/api/whats_new.py`) e `GET /activity` (`backend/app/api/transactions.py`)
alimentavam "O que mudou" e "O que aconteceu", que viraram a caixa de avisos em 2026-10-18
([ADR-027](decisoes/ADR-027-caixa-de-avisos-guardada.md)). O app não as chama mais. Apagar, ou
decidir por escrito que ficam.

### 7 rotas sem contrato de resposta

`SEM_MODELO_HOJE = 7` em `backend/tests/test_contrato_das_rotas.py`. Seguem sem: as quatro de
cobrança, que serão refeitas ([ADR-008](decisoes/ADR-008-monetizacao-por-loja.md)), `/account/export`
(é download de arquivo) e as leituras de operador (`/metrics`, `/analytics/funnel`), cujo formato é
aberto. A lista exata sai de `rotas_declaradas()` menos o contrato gravado.

### 26 · A aparência nos dois temas nunca foi conferida num aparelho

O contraste é verificado por máquina; a aparência não. **Depende de aparelho**, ou emulador com a
pessoa olhando: golden test não substitui, porque a renderização de fonte muda entre o Windows de
quem gera e o Linux do CI.

### 25 · A acessibilidade nunca teve auditoria com leitor de tela

A verificação por máquina cobre alvo de toque de 44dp e ação de toque na semântica
(`alvo_de_toque_test.dart`), alvo rotulado e tamanho nos cinco destinos (`jornada_do_app_test.dart`),
gráfico com tabela equivalente e controles com rótulo (regras 15 e 17). **Falta a auditoria:**
percorrer o app com TalkBack e VoiceOver, o que exige aparelho — e, para iOS, um Mac.

### 27 · A cobrança é backend sem cliente

**Bloqueia só a fase pública.** Existe a cerca, a régua de plano, o preço travado e o webhook — e
nenhuma tela. O que existe hoje **não** será aproveitado: a cobrança será refeita para RevenueCat
([ADR-008](decisoes/ADR-008-monetizacao-por-loja.md)).

### 21 · O mobile nunca teve um release de verdade

**Bloqueia só a fase pública.** O app envia eventos de produto, conferidos contra o catálogo fechado
do servidor, e o README explica como gerar a chave de release. **Falta o que depende de conta:** gerar
e guardar a chave, publicar nas lojas e ver o primeiro evento chegar de um aparelho real.

### Pré-requisitos de loja não atendidos

**Bloqueia só a fase pública.** Não há contas de desenvolvedor Google Play e Apple, nem Mac; o app
nunca rodou em iOS; o botão de Sign in with Apple não existe — o servidor está pronto
(`POST /auth/apple`), e o botão depende de conta Apple Developer, de um Mac e do pacote
`sign_in_with_apple`. Lista completa em [app/operacao](app/operacao.md#publicação-nas-lojas).

### Preço justo de BDR

Não há juro em dólar na base para descontar lucro em dólar
([ADR-014](decisoes/ADR-014-um-modelo-por-classe.md)), e o BDR sai "Sem preço justo". Está em
[05-FUTURO](05-FUTURO.md#considerado).

---

## Base de mercado

### Proventos antigos de BDR, ETF e FII não estão na base

A B3 só dá o histórico de proventos de companhia; de fundo e BDR, cerca de 12 meses antes da
primeira coleta (out/2026). **Faltam os proventos de BDR antes de out/2025**, boa parte dos de ETF, e
os de FII antes de 2016 — de 2016 a out/2025, o mês de FII sem dado da B3 é estimado pelo informe
mensal da CVM. Só entra se vier de outra fonte. Detalhe em
[base/tratamento](base/tratamento.md#eventos-e-proventos).

### A série ajustada ainda tem eventos sem prova

Depois das correções de 2026-10-18, a [revalidação](pesquisa/estudos/validacao-brapi.md) deixou **36
eventos grandes** (fator ≥ 1,5 ou ≤ 0,67) que a brapi lista e a série não ajusta. O dia fica marcado
em `salto_sem_evento` quando o salto passa de 50% ou cai perto de um fator comum — fora disso, não:

- **Antes de 2010** (Bradesco de 2005 a 2008, Gerdau de 2005 e 2006, Ambev, Cosan): não há FRE nem
  IPE para provar. A bonificação de 50% vira queda de 33% **sem marca** — o fator 1,5 ficou fora da
  marca porque, em papel pouco líquido, essa queda é dia comum.
- **Bonificação pequena** (Itaú, Bradesco e Itaúsa, de 2% a 10%, de 2009 a 2025): o FRE mostra o
  fator, mas não a data-com, e o preço não a localiza. Ajustar seria adivinhar o dia.
- **FII sem informe dos dois lados** (237 de 481 saltos marcados): sem a contagem de cotas, não se
  infere; o salto fica marcado.
- **Desdobramento 2:1 com queda abaixo de 45%** (CACR11, −42%): fica fora da faixa de 10% em volta
  do fator 2 e passa sem marca.

Só entra o que tiver prova primária; a brapi aponta, não preenche.

### Proventos e eventos dependem de endpoints da B3 sem contrato

São as únicas fontes não documentadas
([ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md)). Se mudarem, cotação, empresas e
demonstrações continuam, mas a série ajustada para de receber eventos novos — no app, na API de dados
e no laboratório. O disjuntor protege contra queda, não contra descontinuação.

---

## API de dados

### O limite do Pro permite copiar a base pela API

**Bloqueia só a fase pública.** A base não é entregue em arquivo
([ADR-030](decisoes/ADR-030-sem-exportacao-dois-planos.md)), mas o Pro dá 30 mil chamadas por dia,
com páginas de até 5.000 linhas: o histórico de cotações de todos os papéis cabe em poucas horas.
Antes de abrir a terceiros, calibrar limite por dia e tamanho de página para quem testa estratégia,
e não para quem espelha a base, e proibir redistribuição nos termos de uso.

### Abrir a terceiros espera licença, CNPJ e termos de uso

**Bloqueia só a fase pública.** Cobrar espera a resposta da B3 sobre a licença do dado, a leitura da
ODbL da CVM, CNPJ e termos de uso
([ADR-024](decisoes/ADR-024-api-de-dados.md), [ADR-025](decisoes/ADR-025-cobranca-da-api-de-dados.md)).
Com a cobrança aberta, assinar cria a conta, e o e-mail não é verificado: o pagamento é o que
libera a chave ([ADR-031](decisoes/ADR-031-assinatura-cria-a-conta.md)).

---

## Laboratório

### Seis dos oito estudos não têm tela

O painel lê só `registro.jsonl` e `registro_ranking.jsonl`. Calibração, calibração com a taxa nova,
taxa de desconto, custo de troca, filtro de risco e validação contra a brapi aparecem só pelo texto
do protocolo — e a tela *Estudos* diz que os resultados estão em Ranking e Pesquisa de carteira.

---

## Armadilhas conhecidas

Não são bugs, mas mordem. Lista em [06-DESENVOLVIMENTO](06-DESENVOLVIMENTO.md), no
[CLAUDE.md](../CLAUDE.md) da raiz e no de cada parte.
