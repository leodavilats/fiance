# fiance-dados

A base de mercado como serviço, com contas e chaves. É por ela que o backend lê o mercado, com uma
chave do plano `interno`. O que vale para o repositório inteiro está no
[CLAUDE.md da raiz](../CLAUDE.md).

Leitura da área: [ADR-024](../docs/decisoes/ADR-024-api-de-dados.md) ·
[ADR-025](../docs/decisoes/ADR-025-cobranca-da-api-de-dados.md) ·
[11-DADOS-DE-MERCADO](../docs/11-DADOS-DE-MERCADO.md).

```bash
python -m pytest -q                # exige DADOS_API_TEST_DATABASE_URL e ../data-job/requirements.txt
python -m ruff check dadosapi tests migrations
python -m ruff format --check dadosapi tests migrations
```

---

## Invariantes

- **Só lê `mercado`.** Escreve só no schema `acesso`.
- **A chave nunca é guardada, só o hash.**
- **Rota `/admin` exige `DADOS_API_ADMIN_TOKEN`** e não aparece na documentação pública.
- **Coluna nova exige migração Alembic.**
