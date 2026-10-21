# O aplicativo — desenvolvimento

O que vale só para `backend/` e `mobile/`, além do que está em
[06-DESENVOLVIMENTO](../06-DESENVOLVIMENTO.md), que vale para todas as partes.
Última revisão: 2026-10-21

---

## Duas ressalvas que já custaram tempo

**Não rode `dart format`.** O formatter reescreve o `design_tokens.dart` e quebra os `if`s de uma
linha que o repositório mantém.

**O build Android custa minutos, e é o comando que ninguém roda.** `flutter analyze` e `flutter test`
rodam sobre Dart e **nunca** invocam o Gradle: o bump do Kotlin para 2.2 deixou o release Android
quebrado por um plugin preso na linguagem 1.6, com a suíte inteira verde. Rode ao mexer em plugin, em
`pubspec.yaml` ou em qualquer coisa sob `mobile/android/`.

---

## Ao adicionar…

| O quê | Faça também | Senão |
|---|---|---|
| Coluna no model | Migração Alembic em `backend/migrations/` | `test_database_migration.py` falha |
| Tabela com `user_id` | Entrar em `account_store.USER_SCOPED_MODELS` | `test_export_cobre_toda_tabela_com_dono` falha |
| Campo novo numa resposta que o app já lê | Deixá-lo **opcional** no Dart | Versão antiga instalada quebra |
| Campo de dinheiro | Tipo `Money` | `tests/test_money_columns.py` reprova |
| Tela ou rota | Ler [interface](interface.md) antes | O produto se desfaz uma tela por vez |
| Dependência no `pubspec.yaml` | Rodar `flutter build apk --release` | Quebra **só** o build Android |
| Rota pública nova | Decidir por escrito que ela é pública | Sem titular não há teto por usuário |
| Rota nova com `response_model` | Regravar `python -m tests.contrato_das_rotas` | O contrato falha |

---

## Armadilhas do app que não quebram o build

**`_session_global()` em caminho de request** — não filtra por usuário. É para job cross-tenant.

**Dois refreshes simultâneos derrubam a sessão.** O refresh é rotacionado e queimado no uso.

**Escrita seguida de 4xx.** Quem decide commit ou rollback é o **status da resposta**, não a ausência
de exceção — os handlers de `DomainError` vivem no `ExceptionMiddleware` do Starlette, interno ao
middleware de observabilidade. O que precisa sobreviver ao 4xx usa `independent_session()`.

**Rota cara casada por prefixo com versão.** `/api/opportunities` casa, `/api/v1/opportunities` não.
O casamento é por **sufixo**.

**Papel de cor usado como o outro papel.** Direção é `fiDirectionColor`; estado é `fiStateColor`.

---

A jornada do app roda em `flutter test`, sem emulador. **Não cobre** o login Google real nem o
comportamento num aparelho: isso exige conta de loja e aparelho, e fica para o release (ver
[04-PROBLEMAS](../04-PROBLEMAS.md#app), itens 21 e 26).

**Testes de arquitetura e de coerência existem e reprovam:**

| Teste | O que trava |
|---|---|
| `test_entitlement.py` | Condicional de plano fora de `entitlement/`, e importação de `entitlement` pelo cálculo. A lista de camadas falha se uma delas não existir — pasta inexistente não é varrida, e o silêncio passaria |
| `test_regua_nas_duas_plataformas.py` | Os limiares de score do Dart contra os do Python |
| `test_ancoras_da_documentacao.py` | Documentação que cita arquivo ou linha inexistente |
| `test_contrato_das_rotas.py` | Campo de resposta que some, inclusive aninhado; campo de entrada que some ou vira obrigatório (`!`) |
| `test_money_columns.py` | Campo de dinheiro fora do tipo `Money` |
| `test_eventos_do_app_estao_no_catalogo.py` | Evento de produto que o app envia e o servidor não conhece |
| `test_backup_e_restauracao.py` | Backup que não cobre toda tabela, e restauração que ressuscita conta excluída |
| `test_cache_backends.py` | Cache vencido apagado antes da margem de dado velho — falha de rede viraria ausência |

---

## Revisar as telas

```bash
python tool/revisar_telas.py             # catálogo + imagens
python tool/revisar_telas.py --limpar    # apaga a revisão anterior antes
python tool/revisar_telas.py --texto     # só o catálogo, instantâneo
python tool/revisar_telas.py --imagens   # só as capturas
python tool/revisar_telas.py --check     # confere que nada saiu do radar
```

Escreve em `build/revisao/`, que o git ignora. Produz **duas leituras da mesma interface**, porque
nenhuma enxerga o que a outra vê:

| | Como funciona | Enxerga | Não enxerga |
|---|---|---|---|
| `CATALOGO.md` | Lê `mobile/lib/` | Todo o texto do app, inclusive o que só aparece em situação rara; seções, ações, estados e componentes | Nada visual |
| `telas/` | Renderiza e fotografa | Espaçamento, cor, hierarquia; 20 telas × 4 estados × 2 temas (`mobile/captura/telas_test.dart`) | Texto que não está naquele estado |

Sai junto um **`COMO-AVALIAR.md`** com o contexto do produto e as regras que ele já se impôs. Envie-o
sempre: sem ele, quem avalia sugere o contrário do que foi decidido — trocar fio e chão por cards,
remover a proveniência para "limpar a interface".

### O que a captura exigiu, e por quê

- **As fontes são baixadas para `build/revisao/.fontes/`.** O aplicativo usa `google_fonts`, que
  busca a fonte em runtime; em `flutter test` o cliente HTTP é dublado e a busca nunca completa. Sem
  as fontes carregadas por `FontLoader`, o Flutter desenha caixas pretas no lugar do texto — e a
  imagem engana quem for avaliá-la. A fonte de ícones vem do próprio SDK.
- **O plugin de notificação não tem implementação de plataforma sob `flutter test`.** O
  `AppShell` chama `NotificationsService.init()` no primeiro quadro, e o
  `LateInitializationError` que sai dali derrubava a captura de toda tela dentro da casca —
  `/patrimonio` no estado `conteudo` ficou meses sem imagem por isso. A exceção é consumida junto
  com a do `google_fonts`; qualquer outra continua derrubando o teste, e foi assim que o estouro
  de 11 px no cabeçalho do gráfico de evolução apareceu.
- **`toImage` roda dentro de `tester.runAsync`.** Fora dele o Future não completa no relógio falso do
  teste, e cada captura passa a levar **dez minutos** em vez de um segundo.
- **Um `pump` não basta.** Cada Future do Riverpod resolve num ciclo, e tela com providers aninhados
  precisa de mais de um. `pumpAndSettle` não serve: o esqueleto de carregamento anima para sempre.

O arquivo de captura vive em `mobile/captura/`, **fora de `test/`**, de propósito: não é teste de
regressão, e `flutter test` não deve rodá-lo. Ele termina em erro mesmo com as imagens escritas — ao
desenhar um peso que não está nos assets, o `google_fonts` lança depois do fim do teste —, então quem
diz se a captura deu certo são as imagens, e é por elas que o script confere.

⚠️ **Por isso o script apaga `telas/` antes de capturar.** Enquanto ele apenas conferia que *existia*
imagem, uma captura que nem compilava reportava sucesso mostrando a imagem da semana passada — e foi
assim que uma tela apareceu "pronta" com uma correção que não estava nela (2026-09-19). Com a pasta
limpa, o que sobra descreve o código de agora, e captura quebrada deixa a pasta vazia.

**As fixtures vivem em `mobile/test/fixtures/rede_dublada.dart`**, compartilhadas pela captura e
por `fonte_grande_test.dart`. Ao mudar a forma de uma resposta, elas são o segundo lugar a ajustar; se
uma tela aparecer vazia ou em erro na pasta `conteudo/`, é sinal de que a fixture ficou para trás.
