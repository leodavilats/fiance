from fastapi import APIRouter, Depends

from app import affirmation
from app.entitlement import Feature, requires
from app.models import QuickInvestRequest
from app.services import QuickInvestService

router = APIRouter()


# Sem `response_model`: a forma da resposta muda com o modo de afirmação — o
# valor por ativo sai fora do nível prescritivo — e um modelo fixo recusaria
# justamente o rebaixamento que o interruptor existe para permitir.
@router.post(
    "/quick-invest",
    dependencies=[Depends(requires(Feature.QUICK_INVEST))],
)
async def quick_invest(req: QuickInvestRequest) -> dict:
    """Sugestão de aporte, moldada pelo modo de afirmação em vigor.

    Fora do nível prescritivo o valor por ativo sai da resposta e a análise
    fica — é a diferença entre dizer "ponha R$ 500 aqui" e "este é o ativo mais
    distante do preço justo".
    """
    svc = QuickInvestService()
    resultado = await svc.quick_invest(req)
    return affirmation.apply(resultado.model_dump())
