from __future__ import annotations

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fiance.release")


def main() -> int:
    from app.core.config import get_settings
    from app.core.database import engine, migrate

    get_settings().validate_for_startup()

    logger.info("Migrando %s", engine.url.render_as_string(hide_password=True))
    try:
        migrate()
    except Exception:
        logger.exception("Migração falhou — o deploy não deve prosseguir.")
        return 1

    logger.info("Banco na revisão mais recente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
