from __future__ import annotations

import calendar
import secrets
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import httpx
import sqlalchemy as sa

from dadosapi import acesso

LIBERA = {"CONFIRMED", "RECEIVED", "RECEIVED_IN_CASH"}
DESFEITO = {
    "REFUNDED",
    "REFUND_REQUESTED",
    "REFUND_IN_PROGRESS",
    "CHARGEBACK_REQUESTED",
    "CHARGEBACK_DISPUTE",
    "AWAITING_CHARGEBACK_REVERSAL",
}
EVENTOS_DE_PAGAMENTO = {
    "PAYMENT_CONFIRMED",
    "PAYMENT_RECEIVED",
    "PAYMENT_REFUNDED",
    "PAYMENT_REFUND_IN_PROGRESS",
    "PAYMENT_REFUND_DENIED",
    "PAYMENT_RECEIVED_IN_CASH_UNDONE",
    "PAYMENT_CHARGEBACK_REQUESTED",
    "PAYMENT_CHARGEBACK_DISPUTE",
    "PAYMENT_AWAITING_CHARGEBACK_REVERSAL",
    "PAYMENT_DELETED",
    "PAYMENT_RESTORED",
}
EM_ABERTO = ("OVERDUE", "PENDING")
ENCERRADOS = {"SUBSCRIPTION_DELETED", "SUBSCRIPTION_INACTIVATED"}
CICLO_DO_ASAAS = {"mensal": "MONTHLY", "anual": "YEARLY"}
ASSINATURAS_POR_DIA = 3
PARCELAS_NO_ANUAL = 12
EVENTO_PARADO = timedelta(hours=1)
PENDENCIAS_DOS_ULTIMOS = timedelta(days=30)
_PESOS_DO_CNPJ = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


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

    def _pedir(
        self,
        metodo: str,
        rota: str,
        corpo: dict | None = None,
        params: dict | None = None,
        ausente_vale: dict | None = None,
    ) -> dict:
        resposta = self.cliente.request(metodo, rota, json=corpo, params=params)
        if resposta.status_code == 404 and ausente_vale is not None:
            return ausente_vale
        if resposta.is_error:
            raise acesso.SemAcesso(502, f"O Asaas recusou o pedido: {_motivo(resposta)}.")
        return resposta.json()

    def webhook_autentico(self, cabecalho: str | None) -> bool:
        return bool(cabecalho) and secrets.compare_digest(
            cabecalho.encode(), self.token_do_webhook.encode()
        )


@dataclass(frozen=True)
class Pagador:
    nome: str
    documento: str
    cep: str
    numero: str
    telefone: str | None = None


def _dv_do_cpf(digitos: str) -> str:
    soma = sum(int(c) * p for c, p in zip(digitos, range(len(digitos) + 1, 1, -1), strict=True))
    return str(soma * 10 % 11 % 10)


def _dv_do_cnpj(base: str) -> str:
    pesos = _PESOS_DO_CNPJ[-len(base) :]
    resto = sum((ord(c) - 48) * p for c, p in zip(base, pesos, strict=True)) % 11
    return "0" if resto < 2 else str(11 - resto)


def documento_valido(texto: str) -> str | None:
    limpo = "".join(c for c in texto.upper() if c not in " .-/")
    if len(set(limpo)) == 1:
        return None
    if len(limpo) == 11 and limpo.isdigit():
        dv = _dv_do_cpf(limpo[:9])
        return limpo if limpo[9:] == dv + _dv_do_cpf(limpo[:9] + dv) else None
    if len(limpo) == 14 and limpo[:12].isalnum() and limpo[:12].isascii() and limpo[12:].isdigit():
        dv = _dv_do_cnpj(limpo[:12])
        return limpo if limpo[12:] == dv + _dv_do_cnpj(limpo[:12] + dv) else None
    return None


def pagador(
    nome: str | None,
    documento: str | None,
    cep: str | None,
    numero: str | None,
    telefone: str | None,
) -> Pagador | None:
    nome, documento, cep, numero, telefone = (
        (v or "").strip() for v in (nome, documento, cep, numero, telefone)
    )
    if not any((nome, documento, cep, numero, telefone)):
        return None
    if not (nome and documento and cep and numero):
        raise acesso.SemAcesso(422, "Informe nome, CPF ou CNPJ, CEP e número de quem paga.")
    valido = documento_valido(documento)
    if valido is None:
        raise acesso.SemAcesso(422, "CPF ou CNPJ inválido: confira os dígitos.")
    so_digitos = "".join(c for c in cep if c.isdigit())
    if len(so_digitos) != 8 or so_digitos == "0" * 8 or len(cep) > 9:
        raise acesso.SemAcesso(422, "CEP inválido: são oito dígitos.")
    if len(numero) > 10:
        raise acesso.SemAcesso(422, "O número do endereço tem até 10 caracteres.")
    celular = "".join(c for c in telefone if c.isdigit())
    if len(celular) in (12, 13) and celular.startswith("55"):
        celular = celular[2:]
    if telefone and len(celular) not in (10, 11):
        raise acesso.SemAcesso(422, "Telefone com DDD, só os números.")
    return Pagador(nome, valido, so_digitos, numero, celular or None)


def _rota(asaas_id: str, parcelado: bool) -> str:
    return f"/installments/{asaas_id}" if parcelado else f"/subscriptions/{asaas_id}"


def _somar_ciclo(dia: date, ciclo: str) -> date:
    meses = 12 if ciclo == "anual" else 1
    total = dia.month - 1 + meses
    ano, mes = dia.year + total // 12, total % 12 + 1
    return dia.replace(year=ano, month=mes, day=min(dia.day, calendar.monthrange(ano, mes)[1]))


def validar_parcelas(ciclo: str, parcelas: int | None) -> None:
    if parcelas is not None and (ciclo != "anual" or not 2 <= parcelas <= PARCELAS_NO_ANUAL):
        raise acesso.SemAcesso(
            422, f"Só o anual se divide, no cartão, de 2 a {PARCELAS_NO_ANUAL} parcelas."
        )


def criar_assinatura(
    engine: sa.Engine,
    asaas: Asaas,
    conta_id: int,
    plano: str,
    ciclo: str,
    quem_paga: Pagador | None,
    hoje: date | None = None,
    parcelas: int | None = None,
) -> dict:
    validar_parcelas(ciclo, parcelas)
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
        vivas = conn.execute(
            sa.text(
                "SELECT asaas_assinatura, parcelas IS NOT NULL AS parcelado "
                "FROM acesso.assinatura "
                "WHERE conta_id = :id AND situacao IN ('aguardando', 'ativa')"
            ),
            {"id": conta_id},
        ).all()
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
    if quem_paga is None and cliente_anterior is None:
        raise acesso.SemAcesso(422, "Informe nome, CPF ou CNPJ, CEP e número de quem paga.")

    referencia = str(conta_id)
    if quem_paga is None:
        cliente_id = cliente_anterior
    else:
        cadastro = {
            "name": quem_paga.nome,
            "cpfCnpj": quem_paga.documento,
            "email": conta.email,
            "postalCode": quem_paga.cep,
            "addressNumber": quem_paga.numero,
            "externalReference": referencia,
        }
        if quem_paga.telefone:
            cadastro["mobilePhone"] = quem_paga.telefone
        cliente_id = asaas._pedir("POST", "/customers", cadastro)["id"]
    inicio = hoje or acesso.hoje()
    descricao = f"fiance dados — plano {plano}"
    if parcelas is None:
        criada = asaas._pedir(
            "POST",
            "/subscriptions",
            {
                "customer": cliente_id,
                "billingType": "UNDEFINED",
                "value": centavos / 100,
                "nextDueDate": inicio.isoformat(),
                "cycle": CICLO_DO_ASAAS[ciclo],
                "description": descricao,
                "externalReference": referencia,
            },
        )
        asaas_id, pagar_em = criada["id"], None
    else:
        primeira = asaas._pedir(
            "POST",
            "/payments",
            {
                "customer": cliente_id,
                "billingType": "CREDIT_CARD",
                "installmentCount": parcelas,
                "totalValue": centavos / 100,
                "dueDate": inicio.isoformat(),
                "description": f"{descricao}, anual em {parcelas}x",
                "externalReference": referencia,
            },
        )
        asaas_id, pagar_em = primeira["installment"], primeira.get("invoiceUrl")
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO acesso.assinatura (conta_id, plano, ciclo, asaas_cliente, "
                "asaas_assinatura, parcelas, inicio) VALUES (:c, :p, :ci, :cl, :a, :n, :i)"
            ),
            {
                "c": conta_id,
                "p": plano,
                "ci": ciclo,
                "cl": cliente_id,
                "a": asaas_id,
                "n": parcelas,
                "i": inicio if parcelas else None,
            },
        )
        if vivas:
            conn.execute(
                sa.text(
                    "UPDATE acesso.assinatura SET situacao = 'substituida', "
                    "cancelamento_pendente = true WHERE asaas_assinatura = ANY(:a)"
                ),
                {"a": [v.asaas_assinatura for v in vivas]},
            )
    for antiga in vivas:
        _cancelar_no_asaas(engine, asaas, antiga.asaas_assinatura, antiga.parcelado)
    if pagar_em is None:
        try:
            pagar_em = link_em_aberto(asaas, asaas_id, parcelas is not None)
        except (httpx.HTTPError, acesso.SemAcesso):
            pagar_em = None
    return {"assinatura": asaas_id, "pagar_em": pagar_em}


def _cancelar_no_asaas(
    engine: sa.Engine, asaas: Asaas, assinatura_id: str, parcelado: bool
) -> bool:
    try:
        asaas._pedir("DELETE", _rota(assinatura_id, parcelado), ausente_vale={})
    except (httpx.HTTPError, acesso.SemAcesso):
        return False
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "UPDATE acesso.assinatura SET cancelamento_pendente = false "
                "WHERE asaas_assinatura = :a"
            ),
            {"a": assinatura_id},
        )
    return True


def remover_conta(engine: sa.Engine, asaas: Asaas | None, conta_id: int) -> None:
    with engine.connect() as conn:
        ativa = conn.execute(
            sa.text("SELECT ativa FROM acesso.conta WHERE id = :id"), {"id": conta_id}
        ).scalar()
        vivas = conn.execute(
            sa.text(
                "SELECT asaas_assinatura, parcelas IS NOT NULL AS parcelado "
                "FROM acesso.assinatura WHERE conta_id = :id "
                "AND (situacao IN ('aguardando', 'ativa') OR cancelamento_pendente)"
            ),
            {"id": conta_id},
        ).all()
    if ativa is None:
        raise acesso.SemAcesso(404, "Conta não encontrada.")
    if ativa:
        raise acesso.SemAcesso(409, "Desative a conta antes de removê-la.")
    if vivas and asaas is None:
        raise acesso.SemAcesso(
            409,
            "A conta tem assinatura viva no Asaas e a cobrança está desligada: cancele lá antes.",
        )
    for viva in vivas:
        asaas._pedir("DELETE", _rota(viva.asaas_assinatura, viva.parcelado), ausente_vale={})
    acesso.remover_conta(engine, conta_id)


def link_em_aberto(asaas: Asaas, assinatura_id: str, parcelado: bool = False) -> str | None:
    for status in EM_ABERTO:
        cobrancas = (
            asaas._pedir(
                "GET", f"{_rota(assinatura_id, parcelado)}/payments", params={"status": status}
            ).get("data")
            or []
        )
        abertas = sorted(
            (c for c in cobrancas if c.get("status") == status and c.get("invoiceUrl")),
            key=lambda c: str(c.get("dueDate") or ""),
        )
        if abertas:
            return abertas[0]["invoiceUrl"]
    return None


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


def _consultar_pagamento(asaas: Asaas, pagamento_id: str) -> dict:
    return asaas._pedir(
        "GET", f"/payments/{pagamento_id}", ausente_vale={"id": pagamento_id, "deleted": True}
    )


def _aplicar(engine: sa.Engine, asaas: Asaas, tipo: str, corpo: dict) -> str:
    if tipo in EVENTOS_DE_PAGAMENTO:
        pagamento_id = (corpo.get("payment") or {}).get("id")
        if not pagamento_id:
            return "ignorado: pagamento sem id"
        # O corpo do webhook só aponta o pagamento; o estado e o titular saem da consulta.
        return conciliar(engine, asaas, _consultar_pagamento(asaas, pagamento_id))
    if tipo in ENCERRADOS:
        assinatura_id = (corpo.get("subscription") or {}).get("id")
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "UPDATE acesso.assinatura SET situacao = CASE WHEN situacao = 'substituida' "
                    "THEN situacao ELSE 'cancelada' END, cancelamento_pendente = false "
                    "WHERE asaas_assinatura = :a"
                ),
                {"a": assinatura_id},
            )
        return "assinatura cancelada: vale até a data paga"
    return f"ignorado: {tipo}"


def conciliar(engine: sa.Engine, asaas: Asaas, pagamento: dict) -> str:
    pagamento_id = str(pagamento.get("id") or "")
    status = pagamento.get("status")
    removido = bool(pagamento.get("deleted"))
    libera = status in LIBERA and not removido
    if not libera and not removido and status not in DESFEITO:
        return f"ignorado: o Asaas diz {status}"
    with engine.connect() as conn:
        registrado = conn.execute(
            sa.text(
                "SELECT p.situacao, p.vence, s.asaas_assinatura FROM acesso.pagamento p "
                "JOIN acesso.assinatura s ON s.id = p.assinatura_id "
                "WHERE p.asaas_pagamento = :id"
            ),
            {"id": pagamento_id},
        ).first()
        assinatura = conn.execute(
            sa.text(
                "SELECT id, conta_id, plano, ciclo, situacao, parcelas, inicio, asaas_assinatura "
                "FROM acesso.assinatura WHERE asaas_assinatura = :a"
            ),
            {
                "a": pagamento.get("subscription")
                or pagamento.get("installment")
                or (registrado and registrado.asaas_assinatura)
            },
        ).first()
    if assinatura is None:
        return "ignorado: assinatura que não é nossa"
    if pagamento.get("dueDate"):
        vence = date.fromisoformat(pagamento["dueDate"])
    elif registrado is not None:
        vence = registrado.vence
    else:
        return "ignorado: pagamento sem vencimento"
    if libera and assinatura.situacao == "substituida":
        return _estornar_da_substituida(engine, asaas, pagamento_id, assinatura, vence, registrado)
    if libera:
        return _confirmar(engine, pagamento_id, assinatura, vence)
    if registrado is None and status not in DESFEITO and status not in LIBERA:
        return "ignorado: cobrança removida sem pagamento"
    return _desfazer(engine, pagamento_id, assinatura, vence, status or "removida")


def _cobre_ate(assinatura, vence: date) -> date:
    return _somar_ciclo(assinatura.inicio if assinatura.parcelas else vence, assinatura.ciclo)


def _gravar_pagamento(conn, pagamento_id: str, assinatura, vence: date, situacao: str) -> bool:
    return (
        conn.execute(
            sa.text(
                "INSERT INTO acesso.pagamento (asaas_pagamento, assinatura_id, vence, cobre_ate, "
                "situacao) VALUES (:id, :a, :v, :ate, :s) ON CONFLICT (asaas_pagamento) "
                "DO UPDATE SET situacao = excluded.situacao "
                "WHERE acesso.pagamento.situacao <> excluded.situacao RETURNING 1"
            ),
            {
                "id": pagamento_id,
                "a": assinatura.id,
                "v": vence,
                "ate": _cobre_ate(assinatura, vence),
                "s": situacao,
            },
        ).first()
        is not None
    )


def _confirmar(engine: sa.Engine, pagamento_id: str, assinatura, vence: date) -> str:
    with engine.begin() as conn:
        if not _gravar_pagamento(conn, pagamento_id, assinatura, vence, "confirmado"):
            return f"repetido: pagamento já aplicado à conta {assinatura.conta_id}"
        conn.execute(
            sa.text(
                "UPDATE acesso.conta SET "
                "plano = CASE WHEN :ate >= coalesce(pago_ate, :ate) THEN :p ELSE plano END, "
                "pago_ate = greatest(coalesce(pago_ate, :ate), :ate) WHERE id = :c"
            ),
            {
                "p": assinatura.plano,
                "ate": _cobre_ate(assinatura, vence),
                "c": assinatura.conta_id,
            },
        )
        conn.execute(
            sa.text(
                "UPDATE acesso.assinatura SET situacao = :s "
                "WHERE id = :id AND situacao = 'aguardando'"
            ),
            {"s": "quitada" if assinatura.parcelas else "ativa", "id": assinatura.id},
        )
    return f"conta {assinatura.conta_id} no plano {assinatura.plano}"


def _desfazer(engine: sa.Engine, pagamento_id: str, assinatura, vence: date, motivo: str) -> str:
    cobria_ate = _cobre_ate(assinatura, vence)
    with engine.begin() as conn:
        if not _gravar_pagamento(conn, pagamento_id, assinatura, vence, "estornado"):
            return f"repetido: pagamento já desfeito na conta {assinatura.conta_id}"
        if assinatura.parcelas:
            conn.execute(
                sa.text(
                    "UPDATE acesso.pagamento SET situacao = 'estornado' WHERE assinatura_id = :a"
                ),
                {"a": assinatura.id},
            )
        anterior = conn.execute(
            sa.text(
                "SELECT s.plano, p.cobre_ate FROM acesso.pagamento p "
                "JOIN acesso.assinatura s ON s.id = p.assinatura_id "
                "WHERE s.conta_id = :c AND p.situacao = 'confirmado' "
                "ORDER BY p.cobre_ate DESC LIMIT 1"
            ),
            {"c": assinatura.conta_id},
        ).first()
        ate = anterior.cobre_ate if anterior else vence - timedelta(days=1)
        recuou = conn.execute(
            sa.text(
                "UPDATE acesso.conta SET pago_ate = :ate, plano = coalesce(:p, plano) "
                "WHERE id = :c AND pago_ate = :cobria RETURNING id"
            ),
            {
                "ate": ate,
                "p": anterior.plano if anterior else None,
                "c": assinatura.conta_id,
                "cobria": cobria_ate,
            },
        ).first()
    if recuou is None:
        return f"conta {assinatura.conta_id}: pagamento desfeito ({motivo}), o acesso não dependia dele"
    return f"conta {assinatura.conta_id}: pagamento desfeito ({motivo}), pago até {ate}"


def _estornar_da_substituida(
    engine: sa.Engine, asaas: Asaas, pagamento_id: str, assinatura, vence: date, registrado
) -> str:
    if assinatura.parcelas:
        with engine.connect() as conn:
            pedido = conn.execute(
                sa.text(
                    "SELECT 1 FROM acesso.pagamento WHERE assinatura_id = :a "
                    "AND situacao = 'estornado' AND asaas_pagamento <> :id"
                ),
                {"a": assinatura.id, "id": pagamento_id},
            ).first()
        if pedido is not None:
            with engine.begin() as conn:
                _gravar_pagamento(conn, pagamento_id, assinatura, vence, "estornado")
            return f"repetido: estorno do parcelamento já pedido na conta {assinatura.conta_id}"
    if registrado is not None and registrado.situacao == "estornado":
        return (
            f"ignorado: assinatura substituída da conta {assinatura.conta_id}; estornar à mão "
            "(o estorno foi pedido, e o Asaas ainda diz que o pagamento está de pé)"
        )
    try:
        if assinatura.parcelas:
            asaas._pedir("POST", f"{_rota(assinatura.asaas_assinatura, True)}/refund", {})
        else:
            asaas._pedir(
                "POST",
                f"/payments/{pagamento_id}/refund",
                {"description": "Assinatura substituída por outra da mesma conta."},
            )
    except acesso.SemAcesso as erro:
        return (
            f"ignorado: assinatura substituída da conta {assinatura.conta_id}; "
            f"estornar à mão ({erro.mensagem})"
        )
    with engine.begin() as conn:
        _gravar_pagamento(conn, pagamento_id, assinatura, vence, "estornado")
    return f"estornado: pagamento de assinatura substituída da conta {assinatura.conta_id}"


def conferir(engine: sa.Engine, asaas: Asaas, dia: date | None = None) -> dict:
    with engine.connect() as conn:
        vivas = conn.execute(
            sa.text(
                "SELECT asaas_assinatura, parcelas IS NOT NULL AS parcelado "
                "FROM acesso.assinatura WHERE situacao IN ('aguardando', 'ativa')"
            )
        ).all()
        a_cancelar = conn.execute(
            sa.text(
                "SELECT asaas_assinatura, parcelas IS NOT NULL AS parcelado "
                "FROM acesso.assinatura WHERE cancelamento_pendente"
            )
        ).all()
        confirmados = conn.execute(
            sa.text(
                "SELECT asaas_pagamento, cobre_ate FROM acesso.pagamento WHERE situacao = 'confirmado'"
            )
        ).all()
    aplicados: list[str] = []
    falhas: list[str] = []
    for antiga in a_cancelar:
        if _cancelar_no_asaas(engine, asaas, antiga.asaas_assinatura, antiga.parcelado):
            aplicados.append(f"assinatura {antiga.asaas_assinatura} cancelada no Asaas")
        else:
            falhas.append(f"assinatura {antiga.asaas_assinatura}: o Asaas não cancelou")
    conhecidos = {c.asaas_pagamento for c in confirmados}
    vigentes = [c.asaas_pagamento for c in confirmados if c.cobre_ate >= (dia or acesso.hoje())]
    pagamentos: list[dict] = []
    for viva in vivas:
        try:
            for status in sorted(LIBERA):
                pagina = asaas._pedir(
                    "GET",
                    f"{_rota(viva.asaas_assinatura, viva.parcelado)}/payments",
                    params={"status": status, "limit": 100},
                )
                pagamentos += [
                    p for p in pagina.get("data") or [] if str(p.get("id")) not in conhecidos
                ]
        except (httpx.HTTPError, acesso.SemAcesso) as erro:
            falhas.append(f"assinatura {viva.asaas_assinatura}: {erro}")
    for pagamento_id in vigentes:
        try:
            pagamento = _consultar_pagamento(asaas, pagamento_id)
        except (httpx.HTTPError, acesso.SemAcesso) as erro:
            falhas.append(f"pagamento {pagamento_id}: {erro}")
            continue
        if pagamento.get("deleted") or pagamento.get("status") not in LIBERA:
            pagamentos.append(pagamento)
    for pagamento in pagamentos:
        try:
            resultado = conciliar(engine, asaas, pagamento)
        except (httpx.HTTPError, acesso.SemAcesso) as erro:
            falhas.append(f"pagamento {pagamento.get('id')}: {erro}")
            continue
        if not resultado.startswith(("repetido", "ignorado: o Asaas diz")):
            aplicados.append(f"pagamento {pagamento.get('id')}: {resultado}")
    return {
        "em": datetime.now(UTC).isoformat(timespec="seconds"),
        "aplicados": aplicados,
        "falhas": falhas,
    }


def pendencias(engine: sa.Engine) -> list[dict]:
    with engine.connect() as conn:
        linhas = conn.execute(
            sa.text(
                "SELECT id, tipo, recebido_em, resultado FROM acesso.evento_de_cobranca "
                "WHERE (resultado IS NULL AND recebido_em < now() - :parado) "
                "OR (resultado LIKE '%estornar à mão%' AND recebido_em > now() - :janela) "
                "ORDER BY recebido_em DESC"
            ),
            {"parado": EVENTO_PARADO, "janela": PENDENCIAS_DOS_ULTIMOS},
        ).all()
    return [dict(linha._mapping) for linha in linhas]
