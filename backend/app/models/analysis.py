from pydantic import BaseModel, Field

from .enums import AssetType


class FairPriceBlock(BaseModel):
    bazin: float | None = Field(
        None,
        description=(
            "Valor pela distribuição recorrente. Em FII é o método principal; em ação é a "
            "leitura de confirmação, com a mesma taxa do modelo de lucro."
        ),
    )
    graham: float | None = Field(
        None,
        description=(
            "Número de Graham: o limite do critério do investidor defensivo. É indicador, não "
            "entra na faixa — sempre que ele se calcula com o filtro, fica acima do preço."
        ),
    )
    dcf: float | None = Field(
        None,
        description=(
            "Valor central de ação pelo lucro distribuível descontado. O nome é legado: não é "
            "fluxo de caixa livre."
        ),
    )
    consensus: float | None = Field(
        None, description="Valor central do método principal. Não decide nada sozinho."
    )
    fair_low: float | None = Field(
        None,
        description=(
            "Piso da faixa de preço justo: o método principal na premissa pessimista — sem "
            "crescimento e com 1 ponto a mais de taxa. A margem mede contra ele quando o preço "
            "está abaixo."
        ),
    )
    fair_high: float | None = Field(
        None,
        description=(
            "Teto da faixa: o método principal na premissa otimista — com crescimento e 1 ponto "
            "a menos de taxa."
        ),
    )
    band_position: float | None = Field(
        None,
        description=(
            "Onde o preço está dentro da faixa, de 0 no piso a 1 no teto. Nulo quando o preço "
            "está fora dela. Rente ao piso e rente ao teto não são a mesma leitura."
        ),
    )
    band_quality: str = Field(
        "sem_faixa",
        description=(
            "`firme` (faixa estreita e confirmada por outro insumo) · `ampla` (sem confirmação, "
            "confirmação perto da faixa, ou faixa larga) · `fragil` (lucro curto ou instável, "
            "corte de distribuição, ou confirmação que discorda) · `sem_faixa`. Frágil nunca "
            "passa de abaixo ou acima do preço justo."
        ),
    )
    quality_reasons: list[str] = Field(
        default_factory=list, description="O que definiu a qualidade, em frases."
    )
    independent_inputs: int = Field(
        0,
        description=(
            "Quantos insumos distintos sustentam a leitura: o do método principal e, se houver, "
            "o da confirmação."
        ),
    )
    principal: str | None = Field(
        None,
        description=(
            "`lucros_descontados` (ação) · `dividendos` (FII) · nulo quando a classe não tem "
            "método."
        ),
    )
    confirmation: dict | None = Field(
        None,
        description=(
            "A leitura por outro insumo: `method`, `value` e `agreement` — `dentro`, "
            "`fora_ate_30` ou `fora_mais_30` da faixa."
        ),
    )
    premises: dict = Field(
        default_factory=dict,
        description=(
            "As premissas da faixa: taxa, base da taxa, crescimento, ROE, payout, LPA "
            "normalizado, valor sem crescimento e a taxa em que o valor iguala o preço."
        ),
    )
    indicators: list[dict] = Field(
        default_factory=list,
        description=(
            "Indicadores fora da faixa, que não decidem: critério de Graham, preço-teto da "
            "meta de renda da pessoa e P/VP."
        ),
    )
    personal_ceiling: float | None = Field(
        None,
        description=(
            "Preço até o qual a distribuição recorrente rende o yield que a pessoa declarou. "
            "É meta pessoal, não preço justo."
        ),
    )
    methods: list[dict] = Field(
        default_factory=list,
        description=(
            "Diagnóstico por método, com `role` (`principal`, `confirmacao`, `indicador`, "
            "`inaplicavel`) e `status`: `ok`, `inaplicavel`, `sem_dado`, `lucro_negativo`, "
            "`roe_insuficiente`, `sem_juro`, `pouco_distribuido`, `taxa_implausivel`. Silêncios "
            "diferentes têm significados econômicos diferentes."
        ),
    )
    method_dispersion: float | None = None
    methods_disagree: bool = False
    margin_of_safety: float | None = Field(
        None,
        description=(
            "Abaixo do piso: (piso − preço) ÷ piso. Acima do teto: (teto − preço) ÷ preço. "
            "Dentro: 0. As duas pontas medem a mesma distância em escala logarítmica."
        ),
    )
    avg_dividend_5y: float | None = Field(
        None,
        description=(
            "Distribuição recorrente: a média dos anos completos, cada um limitado a 2× a "
            "mediana dos outros, ou a mais recente, se for menor."
        ),
    )
    dy_12m: float | None = None
    dy_5y: float | None = None
    data_years: int = 0
    desired_yield_used: float = 0.06
    pvp: float | None = None
    consensus_methods: int = 0
    details: dict = Field(default_factory=dict)


class TechnicalBlock(BaseModel):
    sma_50: float | None = None
    sma_200: float | None = None
    rsi_14: float | None = None
    trend: str = "unknown"
    trend_basis: str = "none"
    last_price: float | None = None
    distance_from_52w_high_pct: float | None = None
    distance_from_52w_low_pct: float | None = None


class DecisionBlock(BaseModel):
    verdict: str
    label: str
    confidence: float
    confidence_label: str = Field(
        "baixa",
        description=(
            "A confiança em palavra: `alta`, `média` ou `baixa`. A tela mostra esta, e não o "
            "decimal — casa decimal promete precisão que a premissa não entrega."
        ),
    )
    basis: str = Field(
        "band",
        description=(
            "De onde a leitura veio: `band` para a faixa de preço justo, `none` quando não há "
            "faixa. Tendência e RSI nunca decidem: estão no bloco técnico, como contexto."
        ),
    )
    reasons: list[str] = Field(default_factory=list)
    falsifiers: list[dict] = Field(
        default_factory=list,
        description=(
            "O que faria a tese mudar: condições verificáveis, derivadas da mesma régua "
            "lida ao contrário. Lista vazia é resposta legítima — sem preço justo não há "
            "o que ler ao contrário, e inventar uma condição plausível ensinaria a pessoa "
            "a ignorar a seção."
        ),
    )


class PricePoint(BaseModel):
    date: str
    close: float


class AssetAnalysis(BaseModel):
    symbol: str
    asset_type: AssetType
    name: str | None = None
    sector: str | None = None
    currency: str | None = None
    price: float | None = None
    as_of: float | None = Field(
        default=None,
        description=(
            "Momento em que o preço foi lido da fonte, em epoch. O snapshot sempre carregou "
            "este carimbo e ele parava no serviço: a tela julgava um preço sem dizer de quando "
            "ele era, e preço de anteontem muda a decisão."
        ),
    )
    fundamentals: dict = Field(default_factory=dict)
    fair_price: FairPriceBlock
    technical: TechnicalBlock
    decision: DecisionBlock
    price_history: list[PricePoint] = Field(
        default_factory=list,
        description=(
            "Fechamentos diários usados no bloco técnico. Já eram buscados para calcular "
            "médias móveis e descartados em seguida — sem eles o cliente não tem como "
            "desenhar preço contra preço justo. Vem preenchido só no endpoint de um ativo; "
            "em /compare fica vazio, porque N séries completas não cabem numa comparação."
        ),
    )


class CompareResponse(BaseModel):
    items: list[AssetAnalysis] = Field(default_factory=list)
    errors: list[str] = Field(
        default_factory=list, description="Tickers que falharam ao buscar/analisar"
    )
