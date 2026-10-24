# Ferramentas

Escolhidas em 2026-10-24. Preço e limite mudam rápido: confira na página de cada uma antes de assinar
plano anual, e teste um roteiro curto primeiro.

| Papel | Ferramenta | Entra com | Sai com |
|---|---|---|---|
| Avatar falando, voz clonada | **HeyGen** | Vídeo de treino e amostra de voz ([captura](personagem/captura.md)); o roteiro | O Leonardo falando o roteiro, 9:16 |
| Cenas de transição (b-roll) | **Veo 3.1** | Prompt de cena, 9:16 | Clipe de 4 a 8 s |
| Imagem: capa, miniatura, Leonardo em cena | **Nano Banana Pro** | Fotos de referência do rosto; prompt | Imagem estática com o mesmo rosto |
| Montagem | CapCut ou o editor do HeyGen | Avatar, capturas, clipes, legenda | A peça final |

## O que a IA não faz nesta pasta

**Tela, tabela, gráfico ou número do fiance nunca são gerados.** O produto vende dado conferido; uma
resposta JSON inventada num anúncio é exatamente o que ele promete não fazer
([01-VISAO](../docs/01-VISAO.md)). Toda tela vem de captura real do portal, do `/docs` ou de uma
chamada à API.

Também não se gera:

- **logotipo** — vem de [brand/kit/](../brand/kit/); IA redesenha o símbolo e quebra o vão entre o
  chão e a haste que o faz ler F e não E;
- **marca de terceiro** — logotipo da B3, da CVM ou de corretora em cena sugere parceria que não
  existe;
- **gráfico subindo** como ilustração — o laboratório mediu que nada ali antecipa retorno; a imagem
  não promete o que a pesquisa negou.

## Configuração comum

- Formato 9:16, 1080 × 1920, 30 fps.
- Paleta da `fiance-dados`: o `--destaque` do portal (`fiance-dados/dadosapi/paginas/portal.html`),
  verde `#0f8a70` no claro e `#36a989` no escuro.
- Idioma: português do Brasil, nos prompts de voz e nas legendas.
