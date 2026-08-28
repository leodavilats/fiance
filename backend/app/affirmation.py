"""Interruptor de três modos de afirmação.

O produto emite veredito, score e preço justo sobre valores mobiliários. A
Resolução CVM 20 rege a atividade de analista e a 19 sujeita sistemas
automatizados às mesmas obrigações — e **remunerar** julgamento sobre valor
mobiliário aproxima a atividade de prestação de serviço de análise. O
interruptor existe para que a resposta a essa questão seja **configuração**, e
não um refactor sob pressão depois de a consulta jurídica chegar.

Os três modos, em ordem crescente de compromisso:

* **1 — descritivo.** Só o estado da carteira: quanto tem, onde está, quanto
  falta para a meta. Nenhum ativo é apontado.
* **2 — analítico.** O estado mais a leitura de critérios: quais ativos estão
  mais distantes do preço justo, com score e margem de segurança à vista. Diz
  o que a conta mostra. **É o padrão.**
* **3 — prescritivo.** O valor a aportar em cada ativo. É o único modo que
  instrui, e o único que a consulta jurídica pode precisar desligar.

A diferença entre os modos é **estrutural, não textual**. Tentar rebaixar a
afirmação reescrevendo verbo por verbo produz frase ruim e não muda o que
importa: o que caracteriza instrução aqui é o **valor por ativo**, não o modo
verbal do resumo. Então o que sai no nível 2 é o número que diz "ponha tanto
aqui" — e o que fica é toda a análise que sustentava aquele número.

Duas propriedades que valem estar escritas:

* **Rebaixar não esvazia a tela.** No nível 2 os mesmos ativos continuam
  listados, com score, margem de segurança e a distância da meta. Uma
  implementação que escondesse a análise inteira obrigaria a manter o nível 3
  ligado por razões de produto — que é o oposto de um interruptor útil.
* **O nível 3 não combina com personalização por perfil.** Instrução
  individualizada por perfil de investidor é exatamente o que a norma trata
  como consultoria; enquanto não houver parecer, os dois juntos ficam
  bloqueados no código, e não no bom senso de quem configura o ambiente.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from app.core.config import get_settings


class Affirmation(IntEnum):
    DESCRIPTIVE = 1
    ANALYTICAL = 2
    PRESCRIPTIVE = 3


#: Aviso por modo. Vai junto da resposta, para a tela não inventar o seu.
DISCLAIMERS: dict[Affirmation, str] = {
    Affirmation.DESCRIPTIVE: (
        "Este painel descreve a situação da sua carteira. Não avalia ativos individualmente "
        "nem sugere operações."
    ),
    Affirmation.ANALYTICAL: (
        "Leitura de critérios objetivos gerada por sistema automatizado, com a metodologia "
        "à vista em cada número. Não é recomendação de compra ou venda e não considera a sua "
        "situação financeira, seus objetivos nem a sua tolerância a risco."
    ),
    Affirmation.PRESCRIPTIVE: (
        "As sugestões abaixo são geradas automaticamente a partir das metas que você "
        "declarou. Não são recomendação personalizada de investimento e não substituem "
        "análise ou consultoria de profissional habilitado."
    ),
}

#: Campos que **instruem**: dizem quanto pôr onde. São o que sai fora do
#: nível 3 — a análise que os sustenta fica.
ACTION_FIELDS = frozenset(
    {
        "amount",
        "allocated_cash",
        "suggested_amount",
        "quantity",
        "shares",
        "action",
        "action_label",
        "recommended_action",
        "suggested_action",
    }
)

#: Coleções que apontam ativos individualmente. Somem no nível 1, onde só o
#: estado da carteira é afirmado.
ASSET_LEVEL_FIELDS = frozenset(
    {"allocations", "suggestions", "top_buys", "top_sells", "opportunities", "items"}
)


@dataclass(frozen=True)
class Mode:
    level: Affirmation
    disclaimer: str
    #: `False` quando a resposta não deve conter valor por ativo.
    prescriptive: bool
    #: `False` quando a resposta não deve apontar ativos individualmente.
    asset_level: bool
    #: `False` quando o cálculo não deve usar o perfil de risco declarado.
    personalized: bool

    def as_dict(self) -> dict:
        return {
            "level": int(self.level),
            "name": self.level.name.lower(),
            "disclaimer": self.disclaimer,
            "prescriptive": self.prescriptive,
            "asset_level": self.asset_level,
            "personalized": self.personalized,
        }


def current() -> Mode:
    """O modo em vigor, vindo da configuração.

    Valor fora da faixa cai no analítico em vez de estourar: uma variável de
    ambiente digitada errada não pode ligar o modo mais comprometido nem
    derrubar o produto.
    """
    settings = get_settings()

    try:
        nivel = Affirmation(int(settings.affirmation_level))
    except (ValueError, TypeError):
        nivel = Affirmation.ANALYTICAL

    prescritivo = nivel is Affirmation.PRESCRIPTIVE

    return Mode(
        level=nivel,
        disclaimer=DISCLAIMERS[nivel],
        prescriptive=prescritivo,
        asset_level=nivel >= Affirmation.ANALYTICAL,
        # Instrução individualizada por perfil é o que a norma trata como
        # consultoria. Enquanto não houver parecer, os dois juntos ficam
        # bloqueados aqui, e não no bom senso de quem configura o ambiente.
        personalized=not prescritivo or settings.suitability_personalization_allowed,
    )


def apply(payload: dict, mode: Mode | None = None) -> dict:
    """Adapta uma resposta ao modo em vigor.

    Trabalha sobre o dicionário já montado, e não sobre o gerador, porque a
    alternativa seria manter três caminhos de cálculo em sincronia — e o modo
    precisa poder mudar sem que ninguém releia o otimizador.
    """
    modo = mode or current()

    resultado = _walk(payload, modo)
    resultado["affirmation"] = modo.as_dict()
    return resultado


def _walk(value, modo: Mode):
    if isinstance(value, dict):
        saida = {}
        for chave, item in value.items():
            if not modo.asset_level and chave in ASSET_LEVEL_FIELDS:
                saida[chave] = []
                continue
            if not modo.prescriptive and chave in ACTION_FIELDS:
                # Sai o "ponha tanto aqui"; fica o porquê.
                saida[chave] = None
                continue
            saida[chave] = _walk(item, modo)
        return saida

    if isinstance(value, list):
        return [_walk(item, modo) for item in value]

    return value
