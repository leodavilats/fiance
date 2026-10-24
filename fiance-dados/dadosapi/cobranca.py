from __future__ import annotations

import calendar
import secrets
from dataclasses import dataclass
from datetime import date

import httpx
import sqlalchemy as sa

from dadosapi import acesso

CONFIRMADOS = {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}
EM_ABERTO = {"PENDING", "OVERDUE"}
ENCERRADOS = {"SUBSCRIPTION_DELETED", "SUBSCRIPTION_INACTIVATED"}
CICLO_DO_ASAAS = {"mensal": "MONTHLY", "anual": "YEARLY"}
ASSINATURAS_POR_DIA = 3


def _motivo(resposta: httpx.Response) -> str:
    try:
        erros = resposta.json().get("errors") or []
        descricoes = [str(e.get("description")) for e in erros if e.get("description")]
    except (ValueError, AttributeError):
        descricoes = []
    return "; ".join(descricoes) or f"status {resposta.status_code}"


@dataclass(frozen=True)
class Asaas:
    cliente: httpx.Client
    token_do_webhook: str

    @classmethod
    def criar(cls, url: str, chave: str, token_do_webhook: str) -> Asaas:
        cliente = httpx.Client(
            base_url=url.rstrip("/"), headers={"access_token": chave}, timeout=20
        )
        return cls(cliente, token_do_webhook)

    def _pedir(self, metodo: str, rota: str, corpo: dict | None = None) -> dict:
        resposta = self.cliente.request(metodo, rota, json=corpo)
        if resposta.is_error:
            raise acesso.SemAcesso(502, f"O Asaas recusou o pedido: {_motivo(resposta)}.")
        return resposta.json()

    def webhook_autentico(self, cabecalho: str | None) -> bool:
        return bool(cabecalho) and secrets.compare_digest(
            cabecalho.encode(), self.token_do_webhook.encode()
        )


def _somar_ciclo(dia: date, ciclo: str) -> date:
    meses = 12 if ciclo == "anual" else 1
    total = dia.month - 1 + meses
    ano, mes = dia.year + total // 12, total % 12 + 1
    return dia.replace(year=ano, month=mes, day=min(dia.day, calendar.monthrange(ano, mes)[1]))


def criar_assinatura(
    engine: sa.Engine,
    asaas: Asaas,
    conta_id: int,
    plano: str,
    ciclo: str,
    nome: str | None,
    cpf_cnpj: str | None,
    hoje: date | None = None,
) -> dict:
    with engine.connect() as conn:
        conta = conn.execute(
            sa.text("SELECT email FROM acesso.conta WHERE id = :id AND ativa"), {"id": conta_id}
        ).first()
        preco = conn.execute(
            sa.text(
                "SELECT preco_mensal_centavos, preco_anual_centavos FROM acesso.plano "
                "WHERE codigo = :p AND publico"
            ),
            {"p": plano},
        ).first()
        recentes = conn.execute(
            sa.text(
                "SELECT count(*) FROM acesso.assinatura "
                "WHERE conta_id = :id AND criada_em > now() - interval '1 day'"
            ),
            {"id": conta_id},
        ).scalar_one()
        vivas = (
            conn.execute(
                sa.text(
                    "SELECT asaas_assinatura FROM acesso.assinatura "
                    "WHERE conta_id = :id AND situacao IN ('aguardando', 'ativa')"
                ),
                {"id": conta_id},
            )
            .scalars()
            .all()
        )
        cliente_anterior = conn.execute(
            sa.text(
                "SELECT asaas_cliente FROM acesso.assinatura WHERE conta_id = :id "
                "ORDER BY criada_em DESC, id DESC LIMIT 1"
            ),
            {"id": conta_id},
        ).scalar()
    if conta is None:
        raise acesso.SemAcesso(404, "Conta não encontrada ou desativada.")
    if recentes >= ASSINATURAS_POR_DIA:
        raise acesso.SemAcesso(
            429, f"No máximo {ASSINATURAS_POR_DIA} assinaturas por dia. Use o link já enviado."
        )
    centavos = None if preco is None else preco[0 if ciclo == "mensal" else 1]
    if centavos is None:
        raise acesso.SemAcesso(422, f"O plano {plano} não tem cobrança {ciclo} pela página.")
    novo_cadastro = bool(nome and cpf_cnpj)
    if not novo_cadastro and cliente_anterior is None:
        raise acesso.SemAcesso(422, "Informe o nome e o CPF ou CNPJ de quem paga.")

    for antiga in vivas:
        asaas._pedir("DELETE", f"/subscriptions/{antiga}")
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "UPDATE acesso.assinatura SET situacao = 'substituida' "
                    "WHERE asaas_assinatura = :a"
                ),
                {"a": antiga},
            )
    cliente_id = (
        asaas._pedir(
            "POST", "/customers", {"name": nome, "cpfCnpj": cpf_cnpj, "email": conta.email}
        )["id"]
        if novo_cadastro
        else cliente_anterior
    )
    assinatura = asaas._pedir(
        "POST",
        "/subscriptions",
        {
            "customer": cliente_id,
            "billingType": "UNDEFINED",
            "value": centavos / 100,
            "nextDueDate": (hoje or acesso.hoje()).isoformat(),
            "cycle": CICLO_DO_ASAAS[ciclo],
            "description": f"fiance dados — plano {plano}",
        },
    )
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO acesso.assinatura (conta_id, plano, ciclo, asaas_cliente, "
                "asaas_assinatura) VALUES (:c, :p, :ci, :cl, :a)"
            ),
            {"c": conta_id, "p": plano, "ci": ciclo, "cl": cliente_id, "a": assinatura["id"]},
        )
    return {"assinatura": assinatura["id"], "pagar_em": link_em_aberto(asaas, assinatura["id"])}


def link_em_aberto(asaas: Asaas, assinatura_id: str) -> str | None:
    cobrancas = asaas._pedir("GET", f"/subscriptions/{assinatura_id}/payments").get("data") or []
    abertas = sorted(
        (c for c in cobrancas if c.get("status") in EM_ABERTO),
        key=lambda c: str(c.get("dueDate") or ""),
    )
    return abertas[0].get("invoiceUrl") if abertas else None


def processar_evento(engine: sa.Engine, asaas: Asaas, corpo: dict) -> str:
    if not isinstance(corpo, dict):
        return "ignorado: corpo que não é objeto"
    evento_id, tipo = str(corpo.get("id") or ""), str(corpo.get("event") or "")
    if not evento_id or not tipo:
        return "ignorado: evento sem id ou tipo"
    # Evento sem resultado falhou no meio: a reentrega do Asaas o aplica de novo.
    with engine.begin() as conn:
        novo = conn.execute(
            sa.text(
                "INSERT INTO acesso.evento_de_cobranca (id, tipo) VALUES (:id, :t) "
                "ON CONFLICT (id) DO UPDATE SET tipo = excluded.tipo "
                "WHERE acesso.evento_de_cobranca.resultado IS NULL RETURNING id"
            ),
            {"id": evento_id, "t": tipo},
        ).first()
    if novo is None:
        return "repetido"
    resultado = _aplicar(engine, asaas, tipo, corpo)
    with engine.begin() as conn:
        conn.execute(
            sa.text("UPDATE acesso.evento_de_cobranca SET resultado = :r WHERE id = :id"),
            {"r": resultado, "id": evento_id},
        )
    return resultado


def _aplicar(engine: sa.Engine, asaas: Asaas, tipo: str, corpo: dict) -> str:
    if tipo in CONFIRMADOS:
        pagamento_id = (corpo.get("payment") or {}).get("id")
        if not pagamento_id:
            return "ignorado: pagamento sem id"
        # O corpo do webhook só aponta o pagamento; o titular sai da assinatura que nós criamos.
        pagamento = asaas._pedir("GET", f"/payments/{pagamento_id}")
        if pagamento.get("status") not in {"CONFIRMED", "RECEIVED", "RECEIVED_IN_CASH"}:
            return f"ignorado: o Asaas diz {pagamento.get('status')}"
        with engine.begin() as conn:
            assinatura = conn.execute(
                sa.text(
                    "SELECT conta_id, plano, ciclo, situacao FROM acesso.assinatura "
                    "WHERE asaas_assinatura = :a"
                ),
                {"a": pagamento.get("subscription")},
            ).first()
            if assinatura is None:
                return "ignorado: assinatura que não é nossa"
            if assinatura.situacao == "substituida":
                return f"ignorado: assinatura substituída da conta {assinatura.conta_id}; estornar"
            vence = date.fromisoformat(pagamento["dueDate"])
            conn.execute(
                sa.text(
                    "UPDATE acesso.conta SET plano = :p, "
                    "pago_ate = greatest(coalesce(pago_ate, :ate), :ate) WHERE id = :c"
                ),
                {
                    "p": assinatura.plano,
                    "ate": _somar_ciclo(vence, assinatura.ciclo),
                    "c": assinatura.conta_id,
                },
            )
            conn.execute(
                sa.text(
                    "UPDATE acesso.assinatura SET situacao = 'ativa' WHERE asaas_assinatura = :a"
                ),
                {"a": pagamento.get("subscription")},
            )
        return f"conta {assinatura.conta_id} no plano {assinatura.plano}"
    if tipo in ENCERRADOS:
        assinatura_id = (corpo.get("subscription") or {}).get("id")
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "UPDATE acesso.assinatura SET situacao = 'cancelada' "
                    "WHERE asaas_assinatura = :a AND situacao <> 'substituida'"
                ),
                {"a": assinatura_id},
            )
        return "assinatura cancelada: vale até a data paga"
    return f"ignorado: {tipo}"
