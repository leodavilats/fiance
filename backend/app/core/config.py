from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-me"


class InsecureConfigurationError(RuntimeError):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"

    log_level: str = "INFO"

    allowed_origins: str = "http://localhost:4200,http://127.0.0.1:4200"

    database_url: str = "sqlite:///./.cache/fiance.db"

    google_client_id: str = ""

    jwt_secret: str = DEFAULT_JWT_SECRET

    admin_user_ids: str = ""

    rate_limit_enabled: bool = True

    rate_limit_factor: float = 1.0

    entitlements_enabled: bool = False

    affirmation_level: int = 2

    suitability_personalization_allowed: bool = False

    billing_webhook_secret: str = "segredo-de-desenvolvimento"

    brapi_token: str = ""

    brapi_history_range: str = "3mo"

    firebase_service_account_json: str = ""

    default_universe: str = (
        "ITUB4,BBDC4,BBAS3,SANB11,BPAC11,ITSA4,BRSR6,B3SA3,ABCB4,BMGB4,INTER3,"
        "PETR4,PETR3,PRIO3,RECV3,BRAV3,CSAN3,UGPA3,"
        "VALE3,CSNA3,GGBR4,USIM5,GOAU4,GMAT3,CMIN3,FESA4,GGPS3,"
        "EGIE3,EQTL3,CMIG4,CMIG3,CPFE3,TAEE11,ENEV3,ENGI11,AURE3,COCE5,ALUP11,"
        "VIVT3,TIMS3,TELB4,"
        "MGLU3,LREN3,AMER3,PCAR3,ASAI3,SOMA3,BHIA3,GRND3,CEAB3,ALPA4,VULC3,"
        "ABEV3,BEEF3,SMTO3,SLCE3,JALL3,MDIA3,SOJA3,CAML3,LUPA3,"
        "RADL3,RDOR3,HAPV3,FLRY3,QUAL3,DASA3,MATD3,ONCO3,BLAU3,AALR3,HYPE3,PGMN3,LWSA3,"
        "SUZB3,KLBN11,KLBN4,RANI3,"
        "ECOR3,RENT3,VBBR3,SIMH3,LOGN3,TGMA3,EQPA3,RAIL3,"
        "WEGE3,RAIZ4,LEVE3,TUPY3,ROMI3,FRAS3,KEPL3,POMO4,RAPT4,LIGT3,FHER3,PTBL3,"
        "COGN3,YDUQ3,SEER3,ANIM3,VIVA3,"
        "TOTS3,LWSA3,POSI3,SEQL3,IFCM3,DESK3,CASH3,"
        "SLCE3,SOJA3,AGRO3,LAND3,TTEN3,"
        "MRVE3,CYRE3,EZTC3,MULT3,LAVV3,JHSF3,TEND3,DIRR3,HBOR3,EVEN3,TRIS3,LOGG3,PLPL3,MTRE3,PDGR3,"
        "EUCA4,DXCO3,FHER3,PTBL3,MEAL3,"
        "UNIP6,UNIP3,BRKM5,CRPG5,AZEV4,"
        "RAIL3,RADL3,"
        "SAPR11,SBSP3,CSMG3,SAPR4,"
        "CEAB3,AMAR3,DEXP3,VSTE3,CTKA4,TECN3,CAMB3,"
        "ALPA4,IGTI11,HGBS11,SCAR3,MULT3,"
        "BBSE3,CASH3,CXSE3,PINE4,PGMN3,"
        "PSSA3,IRBR3,SMFT3,BBSE3,"
        "UGPA3,CVCB3,NATU3,RSUL4,SHOW3,INTB3,ORVR3,ALPK3,"
        "BRSR6,EVEN3,BGIP4,LUXM4,GGPS3,TCSA3,"
        "AERI3,AGXY3,ALLD3,ALPK3,ARML3,AVLL3,CBAV3,CGAS5,CGRA4,"
        "CSED3,DESK3,DMVF3,DOHL4,EALT4,EMAE4,ENMT4,"
        "FESA4,FIQE3,HBSA3,HOOT4,HYPE3,JFEN3,JSLG3,"
        "LIGT3,LPSB3,MELK3,MILS3,MNPR3,MTSA4,OFSA3,"
        "PRNR3,REDE3,RPMG3,TASA4,TPIS3,"
        "VAMO3,VLID3,WEST3,WLMM4,BAZA3,BEES4,BMOB3,"
        "MOVI3,GEPA4,"
        "HGLG11,MXRF11,KNCR11,KNRI11,XPML11,VISC11,HGRE11,BTLG11,VINO11,RBRR11,HGCR11,GGRC11,TRXF11,RECT11,JSRE11,NEWU11,OUJP11,RCRB11,"
        "HSML11,HGBS11,VILG11,XPML11,FIGS11,ABCP11,PQDP11,"
        "HGRU11,HTMX11,PVBI11,LVBI11,VILG11,GARE11,XPLG11,BRCO11,"
        "HGBS11,VISC11,KNRE11,"
        "ALZR11,BRCR11,RBVA11,KFOF11,MCCI11,TGAR11,URPR11,KNSC11,MAXR11,RBRR11,CPTS11,"
        "HFOF11,DEVA11,CXRI11,KNIP11,VCJR11,VGIR11,RBRP11,"
        "AAPL34,MSFT34,GOGL34,AMZO34,NVDC34,TSLA34,NFLX34,M1TA34,ADBE34,ORCL34,CSCO34,ITLC34,A1MD34,"
        "BABA34,MELI34,EBAY34,PYPL34,"
        "JPMC34,BOAC34,WFCO34,VISA34,"
        "COCA34,PEPB34,NIKE34,SBUB34,ABBV34,MCDC34,"
        "PFIZ34,"
        "EXXO34,"
        "DISB34,W1BD34,INBR32,ROXO34,PAGS34,"
        "BOVA11,BOVV11,SMAL11,IVVB11,PIBB11,DIVO11,GOVE11,MATB11,FIND11,ISUS11,ECOO11,HASH11,BITH11"
    )

    @property
    def universe(self) -> list[str]:
        return [t.strip().upper() for t in self.default_universe.split(",") if t.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env.strip().lower() == "development"

    @property
    def cors_origins(self) -> list[str]:
        if self.is_development:
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        return "*" not in self.cors_origins

    def validate_for_startup(self) -> None:
        if self.is_development:
            return

        if self.jwt_secret == DEFAULT_JWT_SECRET or not self.jwt_secret.strip():
            raise InsecureConfigurationError(
                "JWT_SECRET não configurado (ainda está no valor default 'change-me'). "
                f"Defina JWT_SECRET no ambiente antes de subir com APP_ENV={self.app_env!r}."
            )

        if not self.cors_origins:
            raise InsecureConfigurationError(
                "ALLOWED_ORIGINS vazio fora de development — nenhuma origem poderia "
                "consumir a API. Configure ALLOWED_ORIGINS."
            )

    @property
    def admin_ids(self) -> list[str]:
        return [a.strip() for a in self.admin_user_ids.split(",") if a.strip()]

    @property
    def google_client_ids(self) -> list[str]:
        return [c.strip() for c in self.google_client_id.split(",") if c.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url or "sqlite:///./.cache/fiance.db"
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url


@lru_cache
def get_settings() -> Settings:

    return Settings()
