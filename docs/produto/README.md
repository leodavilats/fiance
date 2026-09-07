# Produto

Para onde o fiance vai. **Nada aqui está construído** — quando vira código, a decisão vira entrada
no [CHANGELOG](../CHANGELOG.md), a regra vira invariante no [CLAUDE.md](../../CLAUDE.md), e o item
sai daqui.

Esta pasta era `planejamento/` na raiz, e era **gitignored**: o roadmap e as decisões de produto
não estavam no repositório. Estão agora.

## Comece por aqui

[VISAO.md](VISAO.md) — as decisões travadas sobre a transformação em andamento. Todo o resto parte
dele.

[ROADMAP.md](ROADMAP.md) — o checklist mestre, por fase, com os portões que são dependência real e
não sugestão de ordem. É também onde mora a tabela de **onde cada decisão já tomada vive**, para a
mesma pergunta não ser reaberta por esquecimento.

## Índice

| Quero saber | Leia |
|---|---|
| As decisões travadas — nome, público, o que preservar, horizonte | [VISAO.md](VISAO.md) |
| A análise que levou a elas — o que a proposta acertava e subestimava | [DIRECAO.md](DIRECAO.md) |
| A fronteira entre o plano grátis e o pago | [MODELO_NEGOCIO.md](MODELO_NEGOCIO.md) |
| As regras de domínio do caixa — dívida, renda, onboarding | [REGRAS_DE_DOMINIO.md](REGRAS_DE_DOMINIO.md) |
| O checklist da transformação, por fase | [ROADMAP.md](ROADMAP.md) |
| O que impede subir, cobrar ou publicar nas lojas — hoje | [PRE_PRODUCAO.md](PRE_PRODUCAO.md) |

## Regras da pasta

- **Um assunto por arquivo.** Bloqueio de go-live é `PRE_PRODUCAO`; a transformação se divide por
  decisão (`VISAO`), negócio (`MODELO_NEGOCIO`), domínio (`REGRAS_DE_DOMINIO`) e execução
  (`ROADMAP`). Nada de arquivo que misture.
- **Pendência não vira histórico.** Ao fechar um item, apague-o ou marque o checkbox. Documento de
  pendência apodrece: este repositório já teve oito de 24 itens falsos numa única revisão do
  `PRE_PRODUCAO`.
- **Nome que envelhece não entra.** Os arquivos se chamavam `VISAO_NOVA`, `REGRAS_NOVO_DOMINIO`,
  `ROADMAP_TRANSFORMACAO` e `ARQUITETURA_INFORMACAO_NOVA` — e "novo" para de ser novo. O que o
  arquivo é já basta.
- **Documento superado se apaga, não se arquiva.** `ARQUITETURA_INFORMACAO_NOVA` foi removido
  porque a decisão que ele preparava está em
  [design/INFORMATION-ARCHITECTURE.md](../design/INFORMATION-ARCHITECTURE.md) — que também registra
  o que foi considerado e recusado — e porque ele passou a **contradizer o código**, argumentando
  contra abandonar o gerador de tokens visuais, coisa que foi feita depois e com motivo escrito.
  Documento que contradiz o código é pior que documento ausente.
- **Painel de status também apodrece.** `ONDE_ESTAMOS` era derivado, se declarava perdedor em
  qualquer divergência, e já estava desatualizado. O estado do trabalho é o `ROADMAP`; o estado do
  sistema é [KNOWN_ISSUES](../KNOWN_ISSUES.md).
- **Nada aqui é invariante.** O que não pode ser violado está no [CLAUDE.md](../../CLAUDE.md) — e é
  para lá que as regras de `REGRAS_DE_DOMINIO` migram quando viram código.
