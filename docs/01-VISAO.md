# Visão

**Fonte de verdade** para o que o fiance é, de que partes é feito e o que cada uma promete. A
visão de cada produto mora na pasta dele.
Última revisão: 2026-10-24

---

## O que é

**O fiance são dois produtos sobre uma base de mercado da B3 montada e mantida aqui**, mais um
laboratório que mede antes de afirmar.

| Parte | O que é | Para quem | Documentos |
|---|---|---|---|
| **App** — `backend/` + `mobile/` | Produto. Onde está cada ativo, e por quê, considerando o que sobra do mês, a carteira e o perfil | Assalariado com pouco tempo, que investe ou quer começar | [app/](app/README.md) |
| **API de dados** — `fiance-dados/` | Produto. A base como serviço, com contas, chaves e planos | Quem testa estratégia ou analisa empresa com dado da B3 e da CVM | [dados/](dados/README.md) |
| **Base de mercado** — `data-job/` | Infraestrutura comum. Coleta diária das fontes oficiais, bruto guardado, versão interpretada no schema `mercado` | Os dois produtos e o laboratório | [base/](base/README.md) |
| **Laboratório** — `fiance-trend/` | Ferramenta do autor, fora dos produtos. Pesquisa com protocolo, e o painel que acompanha base e estudos | O autor | [pesquisa/](pesquisa/README.md) |

```
          fontes oficiais: B3, CVM, BCB, Tesouro
                          │
                    ┌─────▼─────┐
                    │ data-job  │  base de mercado
                    └─────┬─────┘
            ┌─────────────┴──────────────┐
      ┌─────▼────────┐             ┌─────▼────────┐
      │ fiance-dados │             │ fiance-trend │  laboratório
      │ API de dados │             └──────────────┘
      └──┬────────┬──┘
         │        │ chave do plano `interno`
   terceiros   ┌──▼──────────────┐
               │ backend + app   │
               └─────────────────┘
```

O app é o primeiro cliente da API de dados: o que ele lê de mercado passa por ela, com a mesma
chave e os mesmos limites que um terceiro teria. Como as partes se ligam está em
[02-ARQUITETURA](02-ARQUITETURA.md).

---

## Fase atual

**Hoje o fiance tem um usuário: o autor**, que usa o app para investir o próprio dinheiro e o
laboratório para medir o que o app afirma. O público vem depois, sem data
([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)). Na API de dados o acesso é por convite, sem
cobrança.

As regras de produto valem desde já, nos dois produtos.

---

## O que vale para a plataforma inteira

- **Nada de número inventado.** Fonte fora do ar degrada em ordem — cache válido, cache vencido com a
  idade visível, ausência declarada —, e nunca vira estimativa silenciosa. Na base, o dado sem prova
  primária fica marcado, e não preenchido.
- **A idade do dado é informação de primeira linha.** O app carimba a idade na tela; a API diz até
  quando vai cada dado (`/v1/atualidade`); o painel alerta a coleta parada.
- **Fonte oficial e gratuita.** A base vem de arquivos públicos da B3, da CVM, do BCB e do Tesouro
  ([ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md)). Nenhuma API de mercado paga.
- **Medir antes de afirmar.** Estratégia, régua ou premissa que o produto use como sinal passa antes
  por um estudo com protocolo aceito ([pesquisa/](pesquisa/README.md)). O que não passou não vira
  promessa.
- **Não se promete futuro.** Projeção sai em faixa; posição não é previsão de retorno.

## O que já foi medido, e muda o que se pode dizer

| Medida | Resultado | Consequência |
|---|---|---|
| [Calibração do preço justo](pesquisa/estudos/calibracao.md), [refeita com a taxa nova](pesquisa/estudos/calibracao-com-a-taxa-nova.md) | De 2011 a 2017, o veredito do app não ordenou o retorno dos 12 meses seguintes | O app descreve posição, não antecipa retorno |
| [Pesquisa de carteira](pesquisa/estudos/pesquisa.md) | Nenhuma das 8 regras de seleção bateu o CDI por 2 pontos depois de custo e imposto | Seleção por fator não entra em nenhum produto |
| [Ranking de tendência](pesquisa/estudos/ranking.md) | Nenhuma das 6 variações informou o retorno do mês seguinte | A tendência fica como contexto, só no painel |
| [Validação contra a brapi](pesquisa/estudos/validacao-brapi.md) | Eventos que faltavam e saltos sem marca, corrigidos onde havia prova primária | O que segue sem prova está em [04-PROBLEMAS](04-PROBLEMAS.md) |

---

## Modelo de negócio

**Da fase pública, adiada.** Hoje não há receita em nenhum dos dois produtos.

| | App | API de dados |
|---|---|---|
| Modelo | Assinatura, sem gratuidade, trial de 14 dias | Assinatura mensal ou anual, sem plano gratuito: Essencial e Pro. A base não é entregue em arquivo |
| Preço | Até R$ 9,90 por mês | R$ 49 e R$ 149 por mês — hipótese |
| Cobrança | Compra dentro do app, via RevenueCat — não iniciada | Asaas, ligada e usada só pelo autor |
| Condição para cobrar | Publicação nas lojas | Licença de dado da B3, leitura da ODbL da CVM, CNPJ e termos de uso |
| Decisões | [ADR-008](decisoes/ADR-008-monetizacao-por-loja.md), [ADR-009](decisoes/ADR-009-trial-e-gratuidade.md) | [ADR-024](decisoes/ADR-024-api-de-dados.md), [ADR-025](decisoes/ADR-025-cobranca-da-api-de-dados.md), [ADR-030](decisoes/ADR-030-sem-exportacao-dois-planos.md), [ADR-034](decisoes/ADR-034-cobranca-ligada-e-conferida.md) |

Detalhe e hipótese de cada um em [app/produto](app/produto.md#modelo-de-negócio) e
[dados/](dados/README.md#modelo-de-negócio).

## Fora de escopo, em qualquer parte

Não é "ainda não": é **não**. Home broker e execução de ordem; criptomoedas; ações internacionais
diretas, fora de BDR; mercados fora da B3. O que é fora de escopo só para o app está em
[app/produto](app/produto.md#o-que-o-produto-não-é).
