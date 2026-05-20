from __future__ import annotations

from functools import lru_cache

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"

    log_level: str = "INFO"

    brapi_token: str = ""

    gemini_api_key: str = ""

    default_universe: str = (
        # === IBOVESPA - Blue Chips ===
        # Bancos
        "ITUB4,BBDC4,BBAS3,SANB11,BPAC11,ITSA4,BRSR6,B3SA3,"
        # Petróleo e Gás
        "PETR4,PETR3,PRIO3,RECV3,RRRP3,CSAN3,"
        # Mineração
        "VALE3,CSNA3,GGBR4,USIM5,GOAU4,GMAT3,"
        # Energia Elétrica  
        "EGIE3,EQTL3,CMIG4,CMIG3,CPFE3,ENBR3,TAEE11,NEOE3,ENEV3,ENGI11,TRPL4,AURE3,AESB3,TIET11,COCE5,"
        # Telecomunicações
        "VIVT3,TIMS3,"
        # Varejo
        "MGLU3,LREN3,AMER3,PCAR3,ASAI3,CRFB3,SOMA3,VVAR3,LAME4,LAME3,NTCO3,ARZZ3,PETZ3,VIIA3,BHIA3,"
        # Alimentos e Bebidas
        "ABEV3,JBSS3,BRFS3,BEEF3,MRFG3,SMTO3,SLCE3,"
        # Saúde
        "RADL3,RDOR3,HAPV3,GNDI3,FLRY3,QUAL3,DASA3,MATD3,ONCO3,BLAU3,ODPV3,PARD3,AALR3,"
        # Papel e Celulose
        "SUZB3,KLBN11,RANI3,"
        # Infraestrutura e Logística
        "CCRO3,ECOR3,RENT3,VBBR3,SIMH3,LOGN3,WIZS3,TGMA3,"
        # Indústria
        "WEGE3,RAIZ4,EMBR3,LEVE3,TUPY3,ELEK3,ROMI3,FRAS3,KEPL3,POMO4,"
        # Educação
        "COGN3,YDUQ3,SEER3,ANIM3,VIVA3,"
        # Tecnologia e Software
        "TOTVS3,LWSA3,POSI3,SQIA3,TOTS3,MOSI3,SEQL3,IFCM3,"
        
        # === SMALL E MID CAPS ===
        # Construção e Incorporação
        "MRVE3,CYRE3,EZTC3,ALSO3,MULT3,LAVV3,JHSF3,TEND3,DIRR3,HBOR3,EVEN3,TRIS3,RSID3,LOGG3,"
        # Frigoríficos e Proteína
        "MDIA3,BAUH4,TTEN3,SOJA3,CAML3,JALL3,LUPA3,"
        # Materiais de Construção
        "EUCA4,DTEX3,FHER3,PTBL3,TEKA4,PLAS3,MEAL3,TOTS3,"
        # Químmica e Petroquímica
        "UNIP6,BRKM5,PNVL4,CRPG5,ELPL4,AZEV4,GRND3,"
        # Transporte
        "AZUL4,GOLL4,RAIL3,"
        # Utilidades - Saneamento
        "SAPR11,SBSP3,CSMG3,"
        # Vestuário e Têxtil
        "GUAR3,CEAB3,AMAR3,DEXP3,VSTE3,CTKA4,TECN3,CAMB3,HGTX3,"
        # Shopping e Imóveis
        "ALPA4,IGTI11,HGBS11,GSHP3,BRML3,SCAR3,"
        # Serviços Financeiros
        "CIEL3,BBSE3,CASH3,CXSE3,PINE4,BIDI11,CARD3,LCAM3,BPAN4,"
        # Seguros
        "WIZS3,PSSA3,CSAB4,IRBR3,SMFT3,"
        # Serviços Diversos
        "UGPA3,CVCB3,NATU3,CSNA3,RSUL4,SHOW3,ZAMP3,BOBR4,"
        # Holdings e Participações
        "BRSR6,EVEN3,GPAR3,BGIP4,LUXM4,RPAD6,GGPS3,"
        
        # === SMALL CAPS PROMISSORAS ===
        "AERI3,AGXY3,ALLD3,ALPK3,ARML3,ATMP3,AVLL3,BOAS3,BRIT3,CBAV3,CGAS5,CGRA4,CLSA3,"
        "CRDE3,CSED3,CTNM4,CTSA4,DESK3,DMVF3,DOHL4,DTCY3,EALT4,EMAE4,ENMT4,ESTR4,"
        "FESA4,FIQE3,GETT4,GPCP3,HBSA3,HETA4,HOOT4,HYPE3,IGBR3,JFEN3,JPSA3,JSLG3,"
        "KLBN4,LIGT3,LPSB3,MELK3,MILS3,MNPR3,MTRE3,MTSA4,NINJ3,ODER4,OFSA3,ORVR3,"
        "PDGR3,PEAB4,PRNR3,RAPT4,REDE3,RLOG3,RPMG3,SRNA3,STBP3,TASA4,TPIS3,UNIP3,"
        "UNIP5,VAMO3,VLID3,VULC3,WEST3,WLMM4,DMMO3,ENAT3,BMGB4,BAZA3,BEES4,BMOB3,"
        "KRSA3,AGRO3,LAND3,MOVI3,PLPL3,GEPA4,CEPE6,OIBR3,OIBR4,"
        
        # === FIIs - Fundos Imobiliários ===
        "HGLG11,MXRF11,KNCR11,KNRI11,XPML11,VISC11,HGRE11,BTLG11,VINO11,RBRR11,"
        "PVBI11,RECT11,ALZR11,BRCR11,RBVA11,XPLG11,BCFF11,MALL11,HSML11,HFOF11,"
        "KNIP11,HGCR11,HGPO11,CXRI11,TRXF11,GGRC11,HGRU11,HTMX11,HGFF11,KFOF11,"
        "XPPR11,VILG11,JSRE11,RBRF11,DEVA11,MCCI11,TGAR11,URPR11,PATL11,CVBI11,"
        
        # === ADRs/BDRs - Ações Internacionais ===
        # Tech Giants
        "AAPL34,MSFT34,GOOGL34,GOGL34,AMZO34,META34,NVDC34,TSLA34,NFLX34,"
        # Outras empresas US
        "DISB34,BABA34,V1SA34,COCA34,PETR34,MELI34,NIKE34,STNE34,"
        
        # === Criptomoedas ===
        "BTC-USD,ETH-USD,SOL-USD,BNB-USD,XRP-USD,ADA-USD,DOGE-USD,DOT-USD,MATIC-USD,AVAX-USD"
    )

    @property

    def universe(self) -> List[str]:

        return [t.strip().upper() for t in self.default_universe.split(",") if t.strip()]

@lru_cache

def get_settings() -> Settings:

    return Settings()

