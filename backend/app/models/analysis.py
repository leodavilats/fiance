from pydantic import BaseModel, Field

from .enums import AssetType


class FairPriceBlock(BaseModel):
    bazin: float | None = None
    graham: float | None = None
    dcf: float | None = None
    consensus: float | None = None
    fair_low: float | None = Field(
        None,
        description=(
            "Piso da faixa de preço justo: o mais conservador dos métodos que se aplicam. "
            "A margem de segurança é medida contra esta borda quando o preço está abaixo dela."
        ),
    )
    fair_high: float | None = Field(
        None,
        description="Teto da faixa: o mais otimista dos métodos que se aplicam.",
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
            "`firme` (insumos independentes e métodos convergentes) · `ampla` (métodos "
            "discordam) · `fragil` (tudo apoiado num insumo só, inclusive método único) · "
            "`sem_faixa`."
        ),
    )
    independent_inputs: int = Field(
        0,
        description=(
            "Quantos insumos econômicos distintos sustentam a faixa — dividendo, lucro, "
            "patrimônio. Graham e lucros descontados leem o mesmo lucro: três métodos podem "
            "ser duas evidências."
        ),
    )
    methods: list[dict] = Field(
        default_factory=list,
        description=(
            "Diagnóstico por método: `ok`, `inaplicavel`, `sem_dado`, `lucro_negativo`, "
            "`fora_da_faixa` ou `descartado_por_destoar`. Silêncios diferentes têm significados "
            "econômicos diferentes."
        ),
    )
    margin_of_safety: float | None = None
    avg_dividend_5y: float | None = None
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
            "De onde o veredito veio: `band` para a faixa de preço justo, `trend` para leitura "
            "de tendência em ativo sem método aplicável, `none` quando não há nem uma nem outra."
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
