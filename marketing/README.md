# Marketing

O que se diz do fiance para fora, e como se produz. Os vídeos não são gravados: quem fala é o
**Leonardo D'avila gerado por IA** — rosto e voz do autor, clonados ([personagem/](personagem/README.md)).

O que o sistema é e promete está em [docs/](../docs/README.md); esta pasta só traduz isso para
anúncio. Se um roteiro contradiz a documentação, o roteiro está errado.

## Estrutura

Uma pasta por produto, com o nome do sistema. O laboratório (`fiance-trend`) fica fora: é ferramenta
do autor, não produto ([ADR-023](../docs/decisoes/ADR-023-fase-pessoal-primeiro.md)).

| Pasta | O quê | Estado |
|---|---|---|
| [personagem/](personagem/README.md) | Quem fala, como fala, o que nunca diz; como capturar rosto e voz | Guia pronto, captura por fazer |
| [ferramentas.md](ferramentas.md) | O que cada ferramenta de IA faz no fluxo, e o que ela não pode fazer | Escolhidas |
| [fiance-dados/](fiance-dados/README.md) | A API de dados: público, mensagens, provas, roteiros | Posicionamento pronto, roteiros por fazer |
| [fiance-app/](fiance-app/README.md) | O app | Sem conteúdo: não está nas lojas |

A marca não mora aqui. Símbolo, assinatura e logotipo vêm de [brand/kit/](../brand/kit/), gerados
por `brand/build.py`; copiar o desenho para cá cria uma segunda marca
([brand/README.md](../brand/README.md)).

## O que vai para o Git, e o que não vai

**Só texto vai para o repositório:** guias, roteiros, prompts, legendas. Toda mídia fica numa pasta
`midia/` dentro de cada parte, ignorada pelo [.gitignore](.gitignore):

- fotos e vídeo do rosto e amostras de voz — dado biométrico, não sai da máquina nem do HeyGen;
- capturas de tela, imagens e vídeos gerados, exportações finais.

Para guardar a mídia fora da máquina, use um drive pessoal, não o repositório.

## Fluxo de uma peça

1. **Roteiro** em `<produto>/roteiros/`, a partir do [modelo](fiance-dados/roteiros/MODELO.md).
2. **Conferência:** cada afirmação do roteiro tem fonte em `docs/` e passa pelo
   [o que nunca dizer](personagem/README.md#o-que-nunca-dizer).
3. **Capturas reais** do portal, do `/docs` ou de um `curl` contra a API — nunca tela ou número gerado
   por IA.
4. **Avatar** no HeyGen com o roteiro; **cenas de transição** no Veo 3.1; **capa** no Nano Banana Pro.
5. **Montagem** em 9:16, legenda queimada, e o rótulo de IA da plataforma ligado na publicação.

## Canais e formato

Shorts, Reels e TikTok. Vertical 9:16, 1080 × 1920. Duas durações: **30 s** (um gancho, uma ideia) e
**60–90 s** (problema, demonstração, chamada). Tom misto: gancho que um investidor entende,
demonstração que um desenvolvedor respeita.
