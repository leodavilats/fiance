# fiance-trend

Laboratório e painel do autor ([ADR-023](../docs/decisoes/ADR-023-fase-pessoal-primeiro.md)), fora
do app. `backend/` é a pesquisa e a API; `frontend/` é o painel. O que vale para o repositório
inteiro está no [CLAUDE.md da raiz](../CLAUDE.md); o que já foi medido, e com que protocolo, está
em [docs/pesquisa/](../docs/pesquisa/README.md).

```bash
cd backend && python -m pytest -q            # exige ../../backend/requirements.txt instalado
cd backend && python -m ruff check pesquisa api tests
cd backend && python -m ruff format --check pesquisa api tests
cd frontend && npm ci && npm run build && npm test
```

- **A marca é gerada.** `frontend/src/Simbolo.tsx` e `frontend/public/favicon.svg` saem de
  `mobile/tool/build_icons.py`; editados à mão, o CI reprova. O `--destaque` e o `--suave` de
  `estilo.css` são a cor da marca: mudar um pede regerar.
- **A calibração importa `app.*` do backend.** Sem as dependências do backend instaladas, a suíte
  daqui não roda. Mudar o backend pode quebrar esta suíte.
