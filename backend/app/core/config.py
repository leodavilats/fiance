from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"

    log_level: str = "INFO"

    alpha_vantage_key: str = ""

    gemini_api_key: str = ""

    default_universe: str = (
        # === IBOVESPA - Blue Chips ===
        # Bancos e Serviços Financeiros
        "ITUB4,BBDC4,BBAS3,SANB11,BPAC11,ITSA4,BRSR6,B3SA3,ABCB4,BMGB4,INTER3,"
        # Petróleo e Gás
        "PETR4,PETR3,PRIO3,RECV3,BRAV3,CSAN3,UGPA3,"
        # Mineração e Siderurgia
        "VALE3,CSNA3,GGBR4,USIM5,GOAU4,GMAT3,CMIN3,FESA4,GGPS3,"
        # Energia Elétrica
        "EGIE3,EQTL3,CMIG4,CMIG3,CPFE3,TAEE11,ENEV3,ENGI11,AURE3,COCE5,ALUP11,"
        # Telecomunicações
        "VIVT3,TIMS3,TELB4,"
        # Varejo e E-commerce
        "MGLU3,LREN3,AMER3,PCAR3,ASAI3,SOMA3,BHIA3,GRND3,CEAB3,ALPA4,VULC3,"
        # Alimentos e Bebidas
        "ABEV3,BEEF3,SMTO3,SLCE3,JALL3,MDIA3,SOJA3,CAML3,LUPA3,"
        # Saúde e Farmacêutica
        "RADL3,RDOR3,HAPV3,FLRY3,QUAL3,DASA3,MATD3,ONCO3,BLAU3,AALR3,HYPE3,PGMN3,LWSA3,"
        # Papel e Celulose
        "SUZB3,KLBN11,KLBN4,RANI3,"
        # Infraestrutura e Logística
        "ECOR3,RENT3,VBBR3,SIMH3,LOGN3,TGMA3,EQPA3,RAIL3,"
        # Indústria e Manufatura
        "WEGE3,RAIZ4,LEVE3,TUPY3,ROMI3,FRAS3,KEPL3,POMO4,RAPT4,LIGT3,FHER3,PTBL3,"
        # Educação
        "COGN3,YDUQ3,SEER3,ANIM3,VIVA3,"
        # Tecnologia e Software
        "TOTS3,LWSA3,POSI3,SEQL3,IFCM3,DESK3,CASH3,"
        # Agronegócio
        "SLCE3,SOJA3,AGRO3,LAND3,TTEN3,"
        # === SMALL E MID CAPS ===
        # Construção e Incorporação
        "MRVE3,CYRE3,EZTC3,MULT3,LAVV3,JHSF3,TEND3,DIRR3,HBOR3,EVEN3,TRIS3,LOGG3,PLPL3,MTRE3,PDGR3,"
        # Materiais de Construção
        "EUCA4,DXCO3,FHER3,PTBL3,MEAL3,"
        # Química e Petroquímica
        "UNIP6,UNIP3,BRKM5,CRPG5,AZEV4,"
        # Transporte e Logística
        "RAIL3,RADL3,"
        # Utilidades - Saneamento
        "SAPR11,SBSP3,CSMG3,SAPR4,"
        # Vestuário e Têxtil
        "CEAB3,AMAR3,DEXP3,VSTE3,CTKA4,TECN3,CAMB3,"
        # Shopping e Imóveis
        "ALPA4,IGTI11,HGBS11,SCAR3,MULT3,"
        # Serviços Financeiros
        "BBSE3,CASH3,CXSE3,PINE4,PGMN3,"
        # Seguros
        "PSSA3,IRBR3,SMFT3,BBSE3,"
        # Serviços Diversos
        "UGPA3,CVCB3,NATU3,RSUL4,SHOW3,INTB3,ORVR3,ALPK3,"
        # Holdings e Participações
        "BRSR6,EVEN3,BGIP4,LUXM4,GGPS3,TCSA3,"
        # === SMALL CAPS PROMISSORAS ===
        "AERI3,AGXY3,ALLD3,ALPK3,ARML3,AVLL3,CBAV3,CGAS5,CGRA4,"
        "CSED3,DESK3,DMVF3,DOHL4,EALT4,EMAE4,ENMT4,"
        "FESA4,FIQE3,HBSA3,HOOT4,HYPE3,JFEN3,JSLG3,"
        "LIGT3,LPSB3,MELK3,MILS3,MNPR3,MTSA4,OFSA3,"
        "PRNR3,REDE3,RPMG3,TASA4,TPIS3,"
        "VAMO3,VLID3,WEST3,WLMM4,BAZA3,BEES4,BMOB3,"
        "MOVI3,GEPA4,"
        # === FIIs - Fundos Imobiliários ===
        # Tijolo - Lajes Corporativas
        "HGLG11,MXRF11,KNCR11,KNRI11,XPML11,VISC11,HGRE11,BTLG11,VINO11,RBRR11,HGCR11,GGRC11,TRXF11,RECT11,JSRE11,NEWU11,OUJP11,RCRB11,"
        # Tijolo - Shopping
        "HSML11,HGBS11,VILG11,XPML11,FIGS11,ABCP11,PQDP11,"
        # Tijolo - Logística
        "HGRU11,HTMX11,PVBI11,LVBI11,VILG11,GARE11,XPLG11,BRCO11,"
        # Tijolo - Residencial
        "HGBS11,VISC11,KNRE11,"
        # Papel - CRI
        "ALZR11,BRCR11,RBVA11,KFOF11,MCCI11,TGAR11,URPR11,KNSC11,MAXR11,RBRR11,CPTS11,"
        # Híbridos e FOF
        "HFOF11,DEVA11,CXRI11,KNIP11,VCJR11,VGIR11,RBRP11,"
        # === ADRs/BDRs - Ações Internacionais (34 válidos) ===
        # Tech Giants - 13 tickers
        "AAPL34,MSFT34,GOGL34,AMZO34,NVDC34,TSLA34,NFLX34,M1TA34,ADBE34,ORCL34,CSCO34,ITLC34,A1MD34,"
        # E-commerce - 4 tickers
        "BABA34,MELI34,EBAY34,PYPL34,"
        # Financeiro - 4 tickers
        "JPMC34,BOAC34,WFCO34,VISA34,"
        # Consumo - 6 tickers
        "COCA34,PEPB34,NIKE34,SBUB34,ABBV34,MCDC34,"
        # Saúde - 1 ticker
        "PFIZ34,"
        # Energia - 1 ticker
        "EXXO34,"
        # Entretenimento e Fintech - 5 tickers
        "DISB34,W1BD34,INBR32,ROXO34,PAGS34,"
        # === Criptomoedas ===
        "BTC-USD,ETH-USD,SOL-USD,BNB-USD,XRP-USD,ADA-USD,DOGE-USD,DOT-USD,AVAX-USD,LINK-USD,ATOM-USD,LTC-USD,BCH-USD"
    )

    @property
    def universe(self) -> list[str]:

        return [t.strip().upper() for t in self.default_universe.split(",") if t.strip()]


@lru_cache
def get_settings() -> Settings:

    return Settings()
