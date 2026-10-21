# fiance-dados

A base de mercado como serviço, com contas e chaves. É por ela que o backend lê o mercado, com uma
chave do plano `interno`. O que vale para o repositório inteiro está no
[CLAUDE.md da raiz](../CLAUDE.md).

Leitura da área: [docs/dados/](../docs/dados/README.md) · [ADR-024](../docs/decisoes/ADR-024-api-de-dados.md) ·
[ADR-025](../docs/decisoes/ADR-025-cobranca-da-api-de-dados.md) · o que a base tem: [docs/base/](../docs/base/README.md).

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
- **A marca no portal e no console é gerada.** O que está entre `<!-- marca -->` e `<!-- favicon -->`
  sai de `mobile/tool/build_icons.py`; editado à mão, o CI reprova. O `--destaque` e o neutro da
  página (`--tinta-3` no portal, `--suave` no console) são a cor da marca: mudar um pede regerar.
