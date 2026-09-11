import asyncio

from app.analysis.classify import auto_category
from app.collectors import rates
from app.models.quick_invest import (
    FixedIncomeSlice,
    QuickInvestAllocation,
    QuickInvestRequest,
    QuickInvestResponse,
    Unallocated,
)
from app.repositories import AssetRepository, PortfolioRepository
from app.services import GoalService, OpportunityService
from app.services.fixed_income_service import FixedIncomeService

RENDA_FIXA = "renda_fixa"

# Quantos ativos por categoria a sugestão considera. Acima de três a lista deixa de ser uma
# decisão e passa a ser uma triagem, que é o que /descobrir faz.
MAX_POR_CATEGORIA = 3

# O peso de cada posição na categoria, por quantas cabem. Antes era sempre [0.7, 0.2, 0.1], e a
# fatia de 10% caía abaixo da ordem mínima e era descartada em silêncio.
PESOS = {1: (1.0,), 2: (0.6, 0.4), 3: (0.5, 0.3, 0.2)}


class QuickInvestService:
    def __init__(self):
        self.portfolio_repo = PortfolioRepository()
        self.asset_repo = AssetRepository()
        self.goal_service = GoalService()
        self.opportunity_service = OpportunityService()
        self.fixed_income = FixedIncomeService()

    async def quick_invest(self, req: QuickInvestRequest) -> QuickInvestResponse:
        caixa, origem = await self._resolver_caixa(req.cash_available)

        if caixa <= 0:
            return QuickInvestResponse(
                total_cash=0.0,
                cash_source=origem,
                basis="score",
                allocated_cash=0.0,
                remaining_cash=0.0,
                summary=(
                    "Não há sobra para aportar neste mês. A ordem da sobra começa pela dívida "
                    "que custa mais do que sua carteira rende, e ela consome o que entrou."
                ),
            )

        categoria_valores, total_carteira = await self._carteira_por_categoria()

        declaradas = self.goal_service.has_declared_goals()
        metas = (
            {g.category: g.target_pct for g in self.goal_service.get_goals()} if declaradas else {}
        )
        base = "goals" if metas else "score"

        orcamentos = self._orcamento_por_categoria(
            metas=metas,
            categoria_valores=categoria_valores,
            total_carteira=total_carteira,
            caixa=caixa,
        )

        oportunidades = await self._oportunidades()

        alocacoes: list[QuickInvestAllocation] = []
        sem_destino: list[Unallocated] = []
        renda_fixa: FixedIncomeSlice | None = None
        alocado = 0.0

        for categoria, orcamento in orcamentos.items():
            if categoria == RENDA_FIXA:
                renda_fixa = self._fatia_de_renda_fixa(orcamento, metas)
                alocado += orcamento
                continue

            feitas, troco = await self._alocar_categoria(
                categoria=categoria,
                orcamento=orcamento,
                oportunidades=oportunidades,
                min_ordem=req.min_order_value,
                metas=metas,
            )
            alocacoes.extend(feitas)
            alocado += sum(a.suggested_investment for a in feitas)

            if troco > 0:
                sem_destino.append(
                    Unallocated(
                        value=round(troco, 2),
                        reason=self._motivo_do_troco(categoria, feitas, troco, req.min_order_value),
                    )
                )

        return QuickInvestResponse(
            total_cash=round(caixa, 2),
            cash_source=origem,
            basis=base,
            allocated_cash=round(alocado, 2),
            remaining_cash=round(caixa - alocado, 2),
            allocations=alocacoes,
            fixed_income=renda_fixa,
            unallocated=sem_destino,
            portfolio_balance=self._balanco(categoria_valores, alocacoes, renda_fixa, metas),
            summary=self._resumo(alocacoes, renda_fixa, base, sem_destino),
        )

    async def _resolver_caixa(self, informado: float | None) -> tuple[float, str]:
        """Nulo resolve da cascata: o que sobra depois da dívida caseira e da reserva.

        Decidir quanto há para aportar é regra de negócio, e por isso não fica no cliente — os
        dois teriam de repetir "pergunte a sobra, leia available_to_invest", e podiam divergir.
        """
        if informado is not None:
            return informado, "informed"

        from app.services import cashflow_service
        from app.services.rendimento_referencia import referencia_de_rendimento

        mensal, tem_carteira, cdi_anual = await referencia_de_rendimento()
        _, cascata = cashflow_service.sobra(
            referencia_mensal=mensal, tem_carteira=tem_carteira, cdi_anual=cdi_anual
        )
        return float(cascata.as_dict()["available_to_invest"]), "cascade"

    async def _carteira_por_categoria(self) -> tuple[dict[str, float], float]:
        stored = self.portfolio_repo.list_positions()

        async def _snapshot(ticker: str):
            try:
                return await self.asset_repo.get_asset(ticker)
            except Exception:
                return None

        snaps = await asyncio.gather(*[_snapshot(item["ticker"]) for item in stored])

        valores: dict[str, float] = {}
        total = 0.0
        for item, snap in zip(stored, snaps, strict=True):
            if not snap or not snap.price:
                continue
            valor = item["quantity"] * snap.price
            total += valor
            cat = auto_category(snap.asset_type, snap.dividend_yield)
            valores[cat] = valores.get(cat, 0.0) + valor

        rf = sum(
            (p.current_value or p.invested) for p in self.fixed_income.as_portfolio_positions()
        )
        if rf > 0:
            total += rf
            valores[RENDA_FIXA] = valores.get(RENDA_FIXA, 0.0) + rf

        return valores, total

    def _orcamento_por_categoria(
        self,
        *,
        metas: dict[str, float],
        categoria_valores: dict[str, float],
        total_carteira: float,
        caixa: float,
    ) -> dict[str, float]:
        """Quanto vai para cada categoria.

        Sem meta declarada **não se inventa divisão**. Antes o serviço caía num 50/25/25 fixo, que
        é número inventado: nada na carteira da pessoa nem nos objetivos dela dizia isso. Sem meta
        a resposta honesta é ordenar por score num pote único, e dizer que a base é essa.
        """
        if not metas:
            return {"": caixa}

        futuro = total_carteira + caixa
        faltas = {}
        for categoria, alvo_pct in metas.items():
            falta = futuro * (alvo_pct / 100) - categoria_valores.get(categoria, 0.0)
            if falta > 0:
                faltas[categoria] = falta

        if not faltas:
            return {"": caixa}

        soma = sum(faltas.values())
        return {cat: (falta / soma) * caixa for cat, falta in faltas.items()}

    async def _oportunidades(self):
        resposta = await self.opportunity_service.get_opportunities(
            page=1, page_size=30, sort_by="score", sort_order="desc"
        )
        return resposta.items

    async def _alocar_categoria(
        self,
        *,
        categoria: str,
        orcamento: float,
        oportunidades,
        min_ordem: float,
        metas: dict[str, float],
    ) -> tuple[list[QuickInvestAllocation], float]:
        candidatos = [
            opp
            for opp in oportunidades
            if not categoria
            or auto_category(
                opp.asset_type.value if hasattr(opp.asset_type, "value") else str(opp.asset_type),
                opp.dividend_yield,
            )
            == categoria
        ]
        if not candidatos:
            return [], orcamento

        candidatos = sorted(candidatos, key=lambda x: x.score or 0, reverse=True)

        # Quantos cabem respeitando a ordem mínima. Antes o número era fixo em três e as fatias
        # que não alcançavam o mínimo eram descartadas; agora o orçamento decide quantos entram.
        cabem = max(1, int(orcamento // min_ordem)) if min_ordem > 0 else MAX_POR_CATEGORIA
        candidatos = candidatos[: min(len(candidatos), cabem, MAX_POR_CATEGORIA)]
        pesos = PESOS.get(len(candidatos), (1.0,))

        precos = await asyncio.gather(*[self._preco(opp.ticker) for opp in candidatos])

        feitas: list[QuickInvestAllocation] = []
        sobra = orcamento

        for opp, (snap, preco) in zip(candidatos, precos, strict=True):
            if preco is None or preco <= 0:
                continue

            fatia = orcamento * pesos[len(feitas)] if len(feitas) < len(pesos) else 0.0
            fatia = min(fatia, sobra)
            quantidade = int(fatia // preco)
            if quantidade == 0:
                continue

            investido = quantidade * preco
            sobra -= investido
            feitas.append(
                QuickInvestAllocation(
                    ticker=opp.ticker,
                    name=snap.name,
                    category=categoria
                    or auto_category(
                        snap.asset_type
                        if isinstance(snap.asset_type, str)
                        else str(snap.asset_type),
                        snap.dividend_yield,
                    ),
                    sector=snap.sector,
                    current_price=preco,
                    suggested_quantity=quantidade,
                    suggested_investment=round(investido, 2),
                    rationale=self._porque(opp, categoria, metas),
                    score=opp.score,
                    dividend_yield=opp.dividend_yield,
                )
            )

        # O troco de cota inteira volta para a fila: sem isso ele desaparecia sem explicação.
        for indice, alocacao in enumerate(feitas):
            if sobra < alocacao.current_price:
                continue
            extra = int(sobra // alocacao.current_price)
            if extra == 0:
                continue
            investido = extra * alocacao.current_price
            sobra -= investido
            feitas[indice] = alocacao.model_copy(
                update={
                    "suggested_quantity": alocacao.suggested_quantity + extra,
                    "suggested_investment": round(alocacao.suggested_investment + investido, 2),
                }
            )

        return feitas, max(0.0, sobra)

    async def _preco(self, ticker: str):
        try:
            snap = await self.asset_repo.get_asset(ticker)
        except Exception:
            return None, None
        if not snap or not snap.price:
            return snap, None
        return snap, snap.price

    def _fatia_de_renda_fixa(self, orcamento: float, metas: dict[str, float]) -> FixedIncomeSlice:
        """A fatia de renda fixa deixa de desaparecer.

        Ela sumia porque o serviço só olhava a lista de oportunidades, que tem ações, FIIs, BDRs e
        ETFs — nunca um título. Com meta de 25% em renda fixa e R$ 1.000, R$ 250 evaporavam sem
        uma linha na tela.
        """
        mensal: float | None = None
        fonte = "estimativa"
        try:
            lidas = rates.get_rates()
            cdi_anual = lidas.get("cdi_anual")
            fonte = lidas.get("cdi_source", "estimativa")
            if cdi_anual:
                mensal = ((1 + cdi_anual / 100) ** (1 / 12) - 1) * 100
        except Exception:
            pass

        alvo = metas.get(RENDA_FIXA)
        razao = (
            f"Sua alocação-alvo pede {alvo:.0f}% em renda fixa"
            if alvo
            else "Sua alocação-alvo pede renda fixa"
        )
        if mensal is not None:
            razao += f", e a referência rende {mensal:.2f}% ao mês"
        razao += ". Compare títulos antes de escolher — o produto não tem oferta para indicar."

        return FixedIncomeSlice(
            amount=round(orcamento, 2),
            reference_monthly_pct=round(mensal, 4) if mensal is not None else None,
            reference_source=fonte,
            rationale=razao,
        )

    def _motivo_do_troco(
        self,
        categoria: str,
        feitas: list[QuickInvestAllocation],
        troco: float,
        min_ordem: float,
    ) -> str:
        rotulo = categoria or "renda variável"
        if not feitas:
            return (
                f"Nada em {rotulo} passou o filtro de oportunidades com o que sobrou, então este "
                "valor ficou sem destino"
            )
        if troco < min_ordem:
            return f"Troco de cota inteira em {rotulo}: menos que uma ação a mais"
        return f"Em {rotulo} não havia mais ativo cujo preço caiba no que restou"

    def _porque(self, opp, categoria: str, metas: dict[str, float]) -> str:
        razoes = []
        if metas.get(categoria, 0) > 0:
            razoes.append(f"{categoria.replace('_', ' ')} está abaixo da sua meta")
        if opp.score:
            razoes.append(f"score {opp.score:.0f}")
        if opp.dividend_yield and opp.dividend_yield >= 6:
            razoes.append(f"DY {opp.dividend_yield:.1f}%")
        if opp.margin_of_safety and opp.margin_of_safety >= 20:
            razoes.append(f"margem de {opp.margin_of_safety:.0f}%")
        return " · ".join(razoes) if razoes else "entre os melhores scores do universo"

    def _balanco(
        self,
        categoria_valores: dict[str, float],
        alocacoes: list[QuickInvestAllocation],
        renda_fixa: FixedIncomeSlice | None,
        metas: dict[str, float],
    ) -> dict:
        depois = categoria_valores.copy()
        for a in alocacoes:
            depois[a.category] = depois.get(a.category, 0.0) + a.suggested_investment
        if renda_fixa:
            depois[RENDA_FIXA] = depois.get(RENDA_FIXA, 0.0) + renda_fixa.amount

        total = sum(depois.values())
        return {
            cat: {
                "value": round(valor, 2),
                "percentage": round(valor / total * 100, 2) if total > 0 else 0,
                "target": metas.get(cat, 0),
            }
            for cat, valor in depois.items()
        }

    def _resumo(
        self,
        alocacoes: list[QuickInvestAllocation],
        renda_fixa: FixedIncomeSlice | None,
        base: str,
        sem_destino: list[Unallocated],
    ) -> str:
        if not alocacoes and not renda_fixa:
            return (
                "Não encontramos ativo cujo preço caiba neste valor. Um aporte maior, ou uma "
                "ordem mínima menor, abre mais opções."
            )

        partes = []
        n = len(alocacoes)
        if n:
            partes.append(f"{n} {'ativo' if n == 1 else 'ativos'}")
        if renda_fixa:
            partes.append("uma fatia em renda fixa")

        frase = "Esta ordem cobre " + " e ".join(partes) + "."
        frase += (
            " A distribuição sai da sua alocação-alvo."
            if base == "goals"
            else " Sem alocação-alvo declarada, a ordem é por score — declare suas metas para a"
            " distribuição respeitar o que você quer construir."
        )
        if sem_destino:
            # A prosa nunca cita cifra: ela não é varrida pela régua de afirmação, então um
            # número aqui reapareceria depois de o campo ter sido retirado. O valor sem destino
            # viaja em `unallocated`, que é estruturado -- e a frase não diz onde ele aparece,
            # porque "ao lado" é posição de tela e o cliente não tem duas colunas.
            frase += " Parte do valor ficou sem destino, e o motivo vem junto."
        return frase
