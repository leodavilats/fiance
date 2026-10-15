from __future__ import annotations

import calendar
import secrets
from dataclasses import dataclass
from datetime import date

import httpx
import sqlalchemy as sa

from dadosapi import acesso

CONFIRMADOS = {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}
ENCERRADOS = {"SUBSCRIPTION_DELETED", "SUBSCRIPTION_INACTIVATED"}
CICLO_DO_ASAAS = {"mensal": "MONTHLY", "anual": "YEARLY"}


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
            raise acesso.SemAcesso(502, f"O Asaas recusou {rota}: {resposta.text[:200]}")
        return resposta.json()

    def webhook_autentico(self, cabecalho: str | None) -> bool:
        return bool(cabecalho) and secrets.compare_digest(cabecalho, self.token_do_webhook)


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
    nome: str,
    cpf_cnpj: str,
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
    if conta is None:
        raise acesso.SemAcesso(404, "Conta não encontrada ou desativada.")
    centavos = None if preco is None else preco[0 if ciclo == "mensal" else 1]
    if centavos is None:
        raise acesso.SemAcesso(422, f"O plano {plano} não tem cobrança {ciclo} pela página.")

    cliente = asaas._pedir(
        "POST", "/customers", {"name": nome, "cpfCnpj": cpf_cnpj, "email": conta.email}
    )
    assinatura = asaas._pedir(
        "POST",
        "/subscriptions",
        {
            "customer": cliente["id"],
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
            {"c": conta_id, "p": plano, "ci": ciclo, "cl": cliente["id"], "a": assinatura["id"]},
        )
    cobrancas = asaas._pedir("GET", f"/subscriptions/{assinatura['id']}/payments").get("data") or []
    link = cobrancas[0].get("invoiceUrl") if cobrancas else None
    return {"assinatura": assinatura["id"], "pagar_em": link}


def processar_evento(engine: sa.Engine, asaas: Asaas, corpo: dict) -> str:
    evento_id, tipo = str(corpo.get("id") or ""), str(corpo.get("event") or "")
    if not evento_id or not tipo:
        return "ignorado: evento sem id ou tipo"
    with engine.begin() as conn:
        novo = conn.execute(
            sa.text(
                "INSERT INTO acesso.evento_de_cobranca (id, tipo) VALUES (:id, :t) "
                "ON CONFLICT (id) DO NOTHING RETURNING id"
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
                    "SELECT conta_id, plano, ciclo FROM acesso.assinatura "
                    "WHERE asaas_assinatura = :a"
                ),
                {"a": pagamento.get("subscription")},
            ).first()
            if assinatura is None:
                return "ignorado: assinatura que não é nossa"
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
                    "UPDATE acesso.assinatura SET situacao = 'cancelada' WHERE asaas_assinatura = :a"
                ),
                {"a": assinatura_id},
            )
        return "assinatura cancelada: vale até a data paga"
    return f"ignorado: {tipo}"
