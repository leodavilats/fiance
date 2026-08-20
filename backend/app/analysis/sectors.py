from __future__ import annotations

"""Tradução dos setores crus da BRAPI para português.

O backend emitia setor cru nos alertas do dashboard ("Setor Financial Services
concentrado") enquanto o web traduzia setores em todo o resto — a inconsistência
aparecia justamente na tela principal. Mantido em paridade com
`web/src/app/core/services/ui-helper.service.ts` e
`mobile/lib/core/sector_translations.dart`.
"""

_SECTOR_PT: dict[str, str] = {
    # Taxonomia da BRAPI (/quote/list)
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
    # Taxonomia herdada (aparece em respostas antigas em cache)
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
