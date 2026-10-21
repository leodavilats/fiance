# data-job

Coleta de mercado: o único que escreve no `postgres-mercado`. O que vale para o repositório inteiro
está no [CLAUDE.md da raiz](../CLAUDE.md).

Leitura da área: [docs/base/](../docs/base/README.md) · [tratamento](../docs/base/tratamento.md) ·
[ADR-022](../docs/decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md).

```bash
python -m pytest -q                 # gravação exige DATAJOB_TEST_DATABASE_URL
python -m ruff check datajob tests migrations
python -m ruff format --check datajob tests migrations
```

- **O `fiance-dados` roda a suíte dele com o `requirements.txt` daqui.** Dependência nova aqui entra
  na suíte de lá.
- **O `cvm_estimado` é dado de pesquisa.** Ele é gravado aqui, mas não chega ao app.
- **Coluna nova exige migração Alembic.**
