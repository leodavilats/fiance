from __future__ import annotations

_SECTOR_PT: dict[str, str] = {
    "Finance": "Financeiro",
    "Miscellaneous": "Outros",
    "Technology Services": "Tecnologia",
    "Electronic Technology": "Tecnologia",
    "Producer Manufacturing": "Industrial",
    "Industrial Services": "Industrial",
    "Commercial Services": "Industrial",
    "Distribution Services": "Industrial",
    "Transportation": "Industrial",
    "Retail Trade": "Consumo Cíclico",
    "Consumer Services": "Consumo Cíclico",
    "Consumer Durables": "Consumo Cíclico",
    "Consumer Non-Durables": "Consumo Básico",
    "Process Industries": "Materiais Básicos",
    "Non-Energy Minerals": "Materiais Básicos",
    "Health Technology": "Saúde",
    "Health Services": "Saúde",
    "Energy Minerals": "Energia",
    "Utilities": "Utilidades Públicas",
    "Communications": "Telecomunicações",
    "Financial Services": "Financeiro",
    "Technology": "Tecnologia",
    "Healthcare": "Saúde",
    "Energy": "Energia",
    "Basic Materials": "Materiais Básicos",
    "Industrials": "Industrial",
    "Consumer Cyclical": "Consumo Cíclico",
    "Consumer Defensive": "Consumo Básico",
    "Real Estate": "Imobiliário",
    "Communication Services": "Telecomunicações",
}


def translate_sector(sector: str | None) -> str:
    if not sector:
        return "Outros"
    return _SECTOR_PT.get(sector, sector)
