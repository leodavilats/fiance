from __future__ import annotations

import json

from tests.test_contrato_das_rotas import GOLDEN, contrato_atual

if __name__ == "__main__":
    GOLDEN.write_text(
        json.dumps(contrato_atual(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"contrato regravado em {GOLDEN}")
