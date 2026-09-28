# ADR-021 — A exportação da conta volta, e só para conta sem dados financeiros

**Status:** ACEITO
**Data:** 2026-09-28
**Decidido por:** autor do projeto, que pediu a importação; as escolhas abertas estão declaradas aqui

## Contexto

`GET /account/export` entrega tudo o que a conta guarda, em JSON, e é a outra metade da exclusão:
quem exclui leva os dados. Não havia caminho de volta. Quem trocava de login, ou excluía a conta e
depois voltava, tinha de relançar a história inteira à mão.

O arquivo traz as linhas das tabelas da conta, com os `id` e os campos como estavam no banco.

## Problema

Gravar as linhas de volta como vieram furaria as portas únicas de escrita: a posição é projeção do
razão, o caixa passa por `cashflow_service`, o provento no caixa é derivado. E importar sobre uma conta
que já tem dados soma os dois: a mesma compra entra duas vezes, e a carteira dobra.

## Alternativas

1. **Copiar as linhas como vieram.** Rejeitada: posição gravada sem lançamento que a sustente, e
   `id` de outra conta.
2. **Importar sobre conta com dados, marcando duplicidade como na importação de extrato.**
   Rejeitada por ora: caixa, renda fixa e dívida não têm chave de duplicidade, e decidir linha a linha
   o que coincide é trabalho que ninguém pediu.
3. **Importar só em conta sem dados financeiros, cada parte pela sua porta.**

## Decisão

A alternativa 3. `POST /account/import/preview` lê o arquivo e diz o que ele traz, o que fica de fora,
os itens com problema (seção e posição) e o que a conta já tem; `POST /account/import` grava tudo ou
nada, na sessão da requisição.

As escolhas abertas:

- **"Sem dados financeiros"** é: sem lançamento no razão, sem posição nem renda fixa
  (`has_holdings()`), sem provento recebido, sem caixa, sem dívida, sem sugestão seguida.
  Preferências e metas podem existir, e as do arquivo as substituem — a prévia diz isso.
- **O razão é reimportado, e a carteira sai dele** (`ledger_service.import_entries`). Posição do
  arquivo sem nenhum lançamento entra como declaração de posição na data da exportação, com a
  quantidade e o preço médio que tinha. A categoria da posição volta por `rebuild_projection`.
- **Sugestão seguida ligada a um lançamento volta ligada** ao lançamento novo, pelo de-para dos `id`.
- **Dívida quitada volta quitada**, com a data de quitação do dia da importação.
- **Alerta já disparado não volta.** O limite de alertas por conta vale.
- **Fica de fora o que é da conta, e não da pessoa:** aparelhos, eventos de uso, registro de
  atividade, assinatura, indicação, avisos enviados.
- **O arquivo pode vir de outra conta.** Quem manda o próprio arquivo para outra pessoa decide sobre
  os próprios dados; a prévia mostra de qual conta e de quando ele é.
- **Não fica atrás de plano**, como a exportação e a exclusão.

## Consequências

**Ganhos**

- Excluir a conta deixa de ser só de ida: quem volta traz a história de volta
- A carteira importada é a projeção do razão importado, e bate com a apuração
- Erro no arquivo diz onde está, e não grava nada

**Custos aceitos**

- Quem já começou a usar a conta nova não importa sem antes apagar o que lançou
- A data de quitação da dívida e o histórico de disparo do alerta se perdem
- Recorrência de caixa não volta: a tabela existe, e nada a usa hoje

## Referências

- `backend/app/services/account_import_service.py` · `backend/app/api/account.py`
- `backend/tests/test_importar_a_conta.py` · `mobile/test/importar_a_conta_test.dart`
- `mobile/lib/features/config/import_account_screen.dart`, em `/voce/conta/importar`
