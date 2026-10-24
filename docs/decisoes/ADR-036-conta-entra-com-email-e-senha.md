# ADR-036 — A pessoa entra com e-mail e senha, e a chave fica para a máquina

**Status:** ACEITO
**Data:** 2026-10-24
**Decidido por:** autor do projeto
**Ajusta:** [ADR-031](ADR-031-assinatura-cria-a-conta.md) e
[ADR-033](ADR-033-conta-sem-pagamento-entra-em-minha-conta.md), no que a chave faz em Minha conta

## Contexto

A chave era duas coisas: a credencial da máquina, que lê os dados, e o login da pessoa em Minha
conta. Ela aparece uma vez e a base guarda só o hash. Quem a perdia perdia também a conta: não
emitia outra chave nem pagava, e a [ADR-033](ADR-033-conta-sem-pagamento-entra-em-minha-conta.md)
registrou que quem perde a chave antes de pagar fica preso aos sete dias da ADR-031. Uma chave vazada
emitia chaves novas e revogava as do dono.

## Problema

Como deixar quem perdeu a chave voltar à conta, e tirar da chave vazada o poder sobre a conta, sem um
serviço de e-mail?

## Alternativas

1. **Mostrar a chave sempre em Minha conta.** Rejeitada: a base teria de guardar a chave de forma
   recuperável, e um vazamento do banco com o segredo da cifra entregaria todas, a do `interno`
   junto. E não resolve o login: quem perde a chave continua sem entrar.
2. **Login por link no e-mail.** Rejeitada: o serviço não envia e-mail.
3. **E-mail e senha para a pessoa, a chave para a máquina.** A chave continua aparecendo uma vez;
   perdê-la custa um clique em "emitir chave".

## Decisão

A alternativa 3.

- **A senha nasce no cadastro** (`POST /v1/assinatura`), com pelo menos 10 caracteres, guardada em
  scrypt. A resposta já traz a sessão.
- **Entrar abre uma sessão** (`POST /v1/conta/sessao`): `fs_…`, 12 horas, guardada em hash como a
  chave, no mesmo `Authorization: Bearer`. A sessão não lê dado: dado é pela chave, que conta na
  cota. O portal a guarda na aba (`sessionStorage`), como guardava a chave: sem cookie, sem CSRF.
- **Com senha, a chave só consulta a conta.** `GET /v1/conta` aceita a chave; emitir, revogar,
  assinar e trocar a senha pedem a sessão (403 pela chave).
- **Conta sem senha entra pela chave**, como antes, até definir uma (`PUT /v1/conta/senha`). É o
  caminho das contas por convite e das que já existiam.
- **Trocar a senha pede a atual** e encerra todas as sessões.
- **Dez senhas erradas em 15 minutos bloqueiam o e-mail e o endereço**, e e-mail sem conta responde
  igual a senha errada, no mesmo tempo.
- **A administração redefine** (`DELETE /admin/contas/{id}/senha`): apaga a senha e as sessões. A
  pessoa volta a entrar com uma chave, que o autor emite se for preciso, e define outra. A senha nunca
  passa pelo autor.
- **Retomar um cadastro que nunca pagou troca a senha** e derruba as sessões, como já derrubava as
  chaves.

## Consequências

- Esqueci a senha não é automático: passa pelo autor, pelo console. Com a cobrança aberta a
  terceiros, isso pede envio de e-mail.
- O e-mail continua sem verificação ([ADR-031](ADR-031-assinatura-cria-a-conta.md)). A senha não
  muda quem pode criar conta com o e-mail de outra pessoa.
- O bloqueio por e-mail deixa um terceiro trancar o login de alguém por 15 minutos. As chaves seguem
  lendo os dados nesse tempo.
- O bloqueio fica na memória do processo: com mais de uma réplica, cada uma conta o seu.

## Referências

- [docs/dados](../dados/README.md#contas)
- [ADR-031](ADR-031-assinatura-cria-a-conta.md), [ADR-033](ADR-033-conta-sem-pagamento-entra-em-minha-conta.md)
