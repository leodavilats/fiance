# fianceAI — Limitações conhecidas e débito técnico

> Gerado por varredura completa em 2026-08-10.

## Limitações históricas — status atual

| Limitação (registrada em 2026-07) | Status |
|---|---|
| BDR (ex. AAPL34) classificado como `br_stock`; units (SANB11, TAEE11, BPAC11...) classificadas como `fii` | ✅ **Corrigido.** `collectors/universal.py::detect_type()` testa BDR antes de FII; set `KNOWN_UNITS` trata as units conhecidas como `br_stock`; camada extra em `_fetch_brapi` reclassifica por nome (`UNIT/UNT/UNITS`) se necessário. |
| CDI fixo 13,5% no web vs 14,40% no backend | ✅ **Corrigido.** Ambos convergem via `GET /renda-fixa/taxas` → `collectors/rates.py` (BCB SGS real, fallback 14.40). O `signal(14.4)` no Angular é só valor inicial pré-fetch. |
| `fair_price` aplicando Graham em FII | ✅ **Corrigido.** FII usa exclusivamente `[bazin, pvp_fair]`; Graham só roda para ações BR/internacionais. |
| Fundamentos de BDR inconsistentes (LPA/VPA na escala do recibo, não da ação-mãe) | ✅ **Resolvido (validado com dado real em 2026-08-10).** Testado AAPL34 (BRAPI) vs AAPL (Finnhub): a BRAPI já retorna EPS escalado ao próprio preço da BDR (P/E implícito ≈33,8 vs P/E real da Apple ≈35,5 — coerente). `book_value` costuma vir `None` para BDRs na BRAPI (gap de dado, não erro de escala); `graham_fair_price()` já trata isso retornando `None` quando falta book_value, e o DCF segue funcionando só com EPS. Nenhuma correção de código necessária — a causa raiz (yfinance) já não existe mais. |
| Componentes compartilhados (RF form, allocation-view) não extraídos | ⚠️ **Ainda procede no web.** `market.component.html` (1627 linhas), `assets.component.html` (703) e `strategy.component.html` (1030) têm formulários RF/alocação inline sem extração para componentes reutilizáveis. Entre web↔mobile, a única duplicação de lógica de cálculo é o preview de RF (só existe no web). |

## Débito técnico / oportunidades de melhoria

1. **Testes automatizados** — iniciados em 2026-08-10: `backend/tests/` agora cobre as funções puras mais críticas (`analysis/classify.py`, `analysis/fair_price.py`, `analysis/renda_fixa_analysis.py`, `collectors/universal.py::detect_type`), incluindo testes de regressão para os bugs já corrigidos (BDR×FII×unit, FII nunca usa Graham, BDR sem book_value não quebra). 33 testes, todos passando (`pytest` adicionado a `requirements.txt`; rodar com `pytest tests/` dentro de `backend/`). Ainda faltam: `scoring.py`, `dip_analysis.py`, `decision.py`, `strategy.py`, testes de API (routers), e nada no web (`*.spec.ts`) nem no mobile (só o `widget_test.dart` de scaffold).
2. **Prints de debug em produção** — `backend/app/llm/gemini_client.py` usa `print()` com prompt e resposta completos da IA em vez de `logger.debug`, vazando dados para stdout em produção.
3. **Duplicação de regra de negócio (RF)** — `calcularRendimento()`/`calcularValorFinal()` em `assets.component.ts` (alíquotas de IR, juros compostos) replicam `backend/app/analysis/renda_fixa_analysis.py::analyze_one()`. Investigado em 2026-08-10: **não é um preview isolado** — esses métodos alimentam vários `computed()` da tela inteira de Meus Ativos (total investido, valor atual, alocação por tipo, taxa média). Migrar para chamada assíncrona ao backend exigiria reescrever essa cadeia de signals para lidar com estado assíncrono por linha (loading, corrida entre edições), com teste manual completo no navegador — decisão do usuário: manter como está por ora e tratar como item dedicado futuro, não fazer às cegas. Risco aceito: mudança de regra de IR (ex. nova faixa) precisa ser replicada nos dois lados manualmente.
4. **`market.component.html` com 1627 linhas** — maior arquivo do frontend, concentra 3 sub-abas inteiras. Forte candidato a quebra em subcomponentes.
5. **Universo hardcoded como fallback** — `backend/app/core/config.py::default_universe` mantém uma lista de ~400 tickers hardcoded, mesmo já existindo universo dinâmico via BRAPI (`core/universe.py`). É um fallback defensivo intencional, mas extenso.
6. **Rota `/dividends/ranking` intencionalmente desativada** — `backend/app/api/dividends.py` existe mas não está registrada em `backend/app/api/__init__.py`. Decisão do dono do produto (2026-08-10): manter desativada para evitar custo do plano pago da BRAPI (o ranking de dividendos exige mais chamadas). Reativar quando o plano pago for contratado — não remover o código.
7. **BDR sem ajuste de escala** — ver tabela acima, item de fair price de BDR.
8. **Labels/ícones duplicados cross-stack** (`ui-helper.service.ts` no web vs `labels.dart` no mobile) — duplicação estrutural (TS↔Dart não compartilha código nativamente), não um descuido, mas motivo de fricção quando se adiciona um novo AssetType/setor. **Parcialmente mitigado em 2026-08-10** (ver design system, abaixo): as cores agora são idênticas nos dois lados; ainda é preciso lembrar de atualizar os dois arquivos manualmente se um novo AssetType/categoria for adicionado.
9. **Sparklines feitas à mão** (`ui-helper.service.ts`, geração manual de path SVG) em vez de usar uma lib de charting — funciona, mas é mais lógica para manter internamente.

## Unificação visual web↔mobile — Fase 1 (2026-08-10)

Varredura visual completa encontrou: paletas de cor divergentes entre web e mobile (nenhuma cor de marca/ganho/perda/categoria batia, exceto na logo), mobile sem dark mode (tema indigo padrão do Material, não a marca verde/ciano), ícones de navegação diferentes, e uma **inconsistência interna no próprio web** (`categoryBarColor()` tinha FIIs e Cripto trocados em relação a `categoryBarClass`/`categoryColor`).

Ações tomadas (só tokens de design — sem reestruturar telas, por decisão do usuário):
- `web/src/app/core/services/ui-helper.service.ts::categoryBarColor()` corrigido para bater com as outras 3 funções de cor de categoria (FIIs=laranja, Cripto=amarelo).
- `mobile/lib/core/theme.dart` (novo) — tokens espelhando 1:1 as CSS custom properties de `web/src/styles.css` (`--bg`, `--panel`, `--accent`, `--accent-2`, `--warn`, `--danger`, `--radius`), para dark e light. Fonte trocada para Inter (`google_fonts`), igual ao web.
- `mobile/lib/core/theme_provider.dart` (novo) — dark como padrão + toggle persistido (`shared_preferences`), espelhando `theme.service.ts`. Toggle exposto em Configurações.
- `mobile/lib/core/labels.dart` — cores de categoria trocadas para os hex exatos do Tailwind `*-400` usados no web (`acoes_int` e `fiis` e `cripto` estavam com cores erradas: `fiis` era âmbar em vez de laranja, `cripto` era rosa em vez de amarelo).
- Cores de ganho/perda/alerta hardcoded (`Colors.green.shade700`/`Colors.red.shade700`/etc., ~20 ocorrências em 9 arquivos) substituídas por `gainColor()`/`lossColor()`/`warnColor()` do tema — reagem automaticamente ao dark/light mode agora.
- Ícones de navegação (`app_shell.dart`) trocados para os equivalentes Material mais próximos dos ícones Lucide do web (`briefcase`→`work_outline`, `target`→`track_changes_outlined`).
- `pubspec.yaml`: adicionadas `google_fonts` e `shared_preferences`.
- Validado com `flutter analyze` (0 erros, só warnings pré-existentes não relacionados) e `flutter build apk --debug`.

**Não feito nesta fase** (ficou fora do escopo combinado): quebra de `market.component.html` (1627 linhas) e dos arquivos grandes do mobile em componentes menores; padronização de espaçamento/`BoxDecoration` no mobile (ainda cada widget define os próprios valores, sem spacing scale); teste visual manual completo em dispositivo/emulador (recomenda-se rodar `flutter run` e navegar as 4 abas em dark e light antes de considerar fechado).
