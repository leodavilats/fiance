from __future__ import annotations

import hashlib
import secrets
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import sqlalchemy as sa

PREFIXO_DA_CHAVE = "fd_"
TAMANHO_DO_PREFIXO = len(PREFIXO_DA_CHAVE) + 8
PREFIXO_DA_SESSAO = "fs_"
DURACAO_DA_SESSAO = timedelta(hours=12)
_SCRYPT = {"n": 2**14, "r": 8, "p": 1}
_BRT = ZoneInfo("America/Sao_Paulo")
TOLERANCIA_DE_PAGAMENTO = timedelta(days=3)
AVISO_DE_VENCIMENTO = timedelta(days=7)
CADASTRO_AGUARDANDO_PAGAMENTO = timedelta(days=7)
DOMINIO_DA_FUMACA = "@fumaca.invalid"
PAGO_ATE_DA_FUMACA = date(2099, 12, 31)
NOME_DO_RECURSO = {
    "serie": "a série ajustada",
    "ponto_no_tempo": "o balanço como se sabia na data (sabido_em)",
    "informes": "o informe mensal de FII",
}


@dataclass(frozen=True)
class Plano:
    codigo: str
    limite_por_minuto: int
    limite_por_dia: int
    historico_dias: int | None
    chaves_maximas: int
    recursos: frozenset[str] = frozenset()
    pago: bool = False


@dataclass(frozen=True)
class Acesso:
    conta_id: int
    chave_id: int
    prefixo: str
    plano: Plano
    usadas_hoje: int

    @property
    def restantes_hoje(self) -> int:
        return max(self.plano.limite_por_dia - self.usadas_hoje, 0)


class SemAcesso(Exception):
    def __init__(self, status: int, mensagem: str, tentar_em: int | None = None):
        super().__init__(mensagem)
        self.status, self.mensagem, self.tentar_em = status, mensagem, tentar_em


def hoje() -> date:
    return datetime.now(_BRT).date()


def hash_da_chave(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


def gerar_chave() -> tuple[str, str, str]:
    texto = PREFIXO_DA_CHAVE + secrets.token_urlsafe(32)
    return texto, texto[:TAMANHO_DO_PREFIXO], hash_da_chave(texto)


def hash_da_senha(senha: str) -> str:
    sal = secrets.token_bytes(16)
    feito = hashlib.scrypt(senha.encode(), salt=sal, **_SCRYPT)
    return f"scrypt${_SCRYPT['n']}${_SCRYPT['r']}${_SCRYPT['p']}${sal.hex()}${feito.hex()}"


def senha_confere(senha: str, guardado: str | None) -> bool:
    if not guardado:
        hash_da_senha(senha)  # mesmo custo sem senha guardada: o tempo não revela o e-mail
        return False
    _, n, r, p, sal, esperado = guardado.split("$")
    feito = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal), n=int(n), r=int(r), p=int(p))
    return secrets.compare_digest(feito.hex(), esperado)


# Janela fixa por minuto na memória do processo: com mais de uma réplica, cada uma conta a sua.
class LimitePorMinuto:
    def __init__(self, relogio=time.monotonic):
        self._relogio = relogio
        self._contagens: dict[int, tuple[int, int]] = {}
        self._trava = threading.Lock()

    def registrar(self, conta_id: int, limite: int) -> int | None:
        agora = self._relogio()
        minuto = int(agora // 60)
        with self._trava:
            janela, contagem = self._contagens.get(conta_id, (minuto, 0))
            if janela != minuto:
                janela, contagem = minuto, 0
            if contagem >= limite:
                return int(60 - agora % 60) + 1
            self._contagens[conta_id] = (janela, contagem + 1)
        return None


class Tentativas:
    def __init__(self, maximo: int = 10, janela: float = 900.0, relogio=time.monotonic):
        self._maximo, self._janela, self._relogio = maximo, janela, relogio
        self._falhas: dict[str, list[float]] = {}
        self._trava = threading.Lock()

    def bloqueado(self, origem: str) -> bool:
        agora = self._relogio()
        with self._trava:
            recentes = [t for t in self._falhas.get(origem, []) if agora - t < self._janela]
            if recentes:
                self._falhas[origem] = recentes
            else:
                self._falhas.pop(origem, None)
            return len(recentes) >= self._maximo

    def registrar(self, origem: str) -> None:
        with self._trava:
            self._falhas.setdefault(origem, []).append(self._relogio())


def situacao_da_conta(ativa: bool, pago: bool, pago_ate: date | None, dia: date) -> str:
    if not ativa:
        return "desativada"
    if not pago:
        return "ativa"
    if pago_ate is None or pago_ate + TOLERANCIA_DE_PAGAMENTO < dia:
        return "sem_pagamento"
    if pago_ate < dia:
        return "em_tolerancia"
    if pago_ate - dia <= AVISO_DE_VENCIMENTO:
        return "a_vencer"
    return "ativa"


def _situacao(linha, dia: date) -> str:
    situacao = situacao_da_conta(linha.ativa, linha.plano_pago, linha.pago_ate, dia)
    if situacao == "sem_pagamento" and linha.pago_ate is None and linha.aguardando:
        return "aguardando_pagamento"
    return situacao


_AGUARDANDO = (
    "EXISTS (SELECT 1 FROM acesso.assinatura s WHERE s.conta_id = c.id "
    "AND s.situacao = 'aguardando') AS aguardando"
)


_CHAVE_VALIDA = sa.text(
    """
    SELECT k.id AS chave_id, k.prefixo, c.id AS conta_id, c.pago_ate, p.codigo,
        p.limite_por_minuto, p.limite_por_dia, p.historico_dias, p.chaves_maximas, p.recursos,
        p.preco_mensal_centavos, c.senha_hash IS NOT NULL AS tem_senha
    FROM acesso.chave k
    JOIN acesso.conta c ON c.id = k.conta_id
    JOIN acesso.plano p ON p.codigo = c.plano
    WHERE k.hash = :hash AND k.revogada_em IS NULL AND c.ativa
    """
)

_CONTAR_USO = sa.text(
    """
    WITH contado AS (
        INSERT INTO acesso.uso_diario (chave_id, dia, requisicoes) VALUES (:chave, :dia, 1)
        ON CONFLICT (chave_id, dia) DO UPDATE SET requisicoes = acesso.uso_diario.requisicoes + 1
        RETURNING requisicoes
    )
    SELECT (SELECT requisicoes FROM contado) + coalesce((
        SELECT sum(u.requisicoes) FROM acesso.uso_diario u
        JOIN acesso.chave k ON k.id = u.chave_id
        WHERE k.conta_id = :conta AND u.dia = :dia AND u.chave_id <> :chave
    ), 0)
    """
)


def autenticar(
    engine: sa.Engine, texto: str | None, por_minuto: LimitePorMinuto, dia: date | None = None
) -> Acesso:
    if not texto or not texto.startswith(PREFIXO_DA_CHAVE):
        raise SemAcesso(
            401, "Chave ausente ou em formato inválido. Envie Authorization: Bearer <chave>."
        )
    with engine.begin() as conn:
        linha = conn.execute(_CHAVE_VALIDA, {"hash": hash_da_chave(texto)}).first()
        if linha is None:
            raise SemAcesso(401, "Chave desconhecida, revogada, ou de conta desativada.")
        plano = Plano(
            linha.codigo,
            linha.limite_por_minuto,
            linha.limite_por_dia,
            linha.historico_dias,
            linha.chaves_maximas,
            frozenset(linha.recursos or ()),
            linha.preco_mensal_centavos is not None,
        )
        dia_de_hoje = dia or hoje()
        if situacao_da_conta(True, plano.pago, linha.pago_ate, dia_de_hoje) == "sem_pagamento":
            raise SemAcesso(402, "A assinatura da conta está vencida ou não foi paga.")
        espera = por_minuto.registrar(linha.conta_id, plano.limite_por_minuto)
        if espera is not None:
            raise SemAcesso(429, "Limite por minuto atingido.", tentar_em=espera)
        usadas = conn.execute(
            _CONTAR_USO, {"chave": linha.chave_id, "conta": linha.conta_id, "dia": dia_de_hoje}
        ).scalar_one()
        conn.execute(
            sa.text("UPDATE acesso.chave SET ultimo_uso_em = now() WHERE id = :id"),
            {"id": linha.chave_id},
        )
    if usadas > plano.limite_por_dia:
        raise SemAcesso(429, "Limite do dia atingido. Ele volta à meia-noite de Brasília.")
    return Acesso(linha.conta_id, linha.chave_id, linha.prefixo, plano, usadas)


_SESSAO_VALIDA = sa.text(
    """
    SELECT s.conta_id FROM acesso.sessao s JOIN acesso.conta c ON c.id = s.conta_id
    WHERE s.hash = :hash AND s.expira_em > now() AND c.ativa
    """
)


def entrar(engine: sa.Engine, texto: str | None, *, so_consulta: bool = False) -> int:
    if texto and texto.startswith(PREFIXO_DA_SESSAO):
        with engine.connect() as conn:
            conta_id = conn.execute(_SESSAO_VALIDA, {"hash": hash_da_chave(texto)}).scalar()
        if conta_id is None:
            raise SemAcesso(401, "Sessão vencida ou encerrada. Entre de novo com e-mail e senha.")
        return conta_id
    if not texto or not texto.startswith(PREFIXO_DA_CHAVE):
        raise SemAcesso(
            401, "Entre com e-mail e senha, ou envie a chave em Authorization: Bearer <chave>."
        )
    with engine.connect() as conn:
        linha = conn.execute(_CHAVE_VALIDA, {"hash": hash_da_chave(texto)}).first()
    if linha is None:
        raise SemAcesso(401, "Chave desconhecida, revogada, ou de conta desativada.")
    if linha.tem_senha and not so_consulta:
        raise SemAcesso(
            403, "Esta conta entra com e-mail e senha: pela chave, ela só consulta a conta."
        )
    return linha.conta_id


def nova_sessao(engine: sa.Engine, conta_id: int) -> dict:
    texto = PREFIXO_DA_SESSAO + secrets.token_urlsafe(32)
    with engine.begin() as conn:
        conn.execute(
            sa.text("DELETE FROM acesso.sessao WHERE conta_id = :c AND expira_em <= now()"),
            {"c": conta_id},
        )
        expira_em = conn.execute(
            sa.text(
                "INSERT INTO acesso.sessao (conta_id, hash, expira_em) "
                "VALUES (:c, :h, now() + :duracao) RETURNING expira_em"
            ),
            {"c": conta_id, "h": hash_da_chave(texto), "duracao": DURACAO_DA_SESSAO},
        ).scalar_one()
    return {"sessao": texto, "expira_em": expira_em}


def entrar_com_senha(engine: sa.Engine, email: str, senha: str) -> dict:
    with engine.connect() as conn:
        conta = conn.execute(
            sa.text(
                "SELECT id, senha_hash FROM acesso.conta WHERE lower(email) = lower(:e) AND ativa"
            ),
            {"e": email.strip()},
        ).first()
    if not senha_confere(senha, conta.senha_hash if conta else None):
        raise SemAcesso(401, "E-mail ou senha incorretos.")
    return nova_sessao(engine, conta.id)


def encerrar_sessao(engine: sa.Engine, texto: str | None) -> None:
    if texto and texto.startswith(PREFIXO_DA_SESSAO):
        with engine.begin() as conn:
            conn.execute(
                sa.text("DELETE FROM acesso.sessao WHERE hash = :h"), {"h": hash_da_chave(texto)}
            )


def definir_senha(engine: sa.Engine, conta_id: int, nova: str, atual: str | None) -> dict:
    with engine.connect() as conn:
        guardada = conn.execute(
            sa.text("SELECT senha_hash FROM acesso.conta WHERE id = :id"), {"id": conta_id}
        ).scalar()
    if guardada is not None and not senha_confere(atual or "", guardada):
        raise SemAcesso(403, "A senha atual não confere.")
    with engine.begin() as conn:
        conn.execute(
            sa.text("UPDATE acesso.conta SET senha_hash = :s WHERE id = :id"),
            {"s": hash_da_senha(nova), "id": conta_id},
        )
        conn.execute(sa.text("DELETE FROM acesso.sessao WHERE conta_id = :id"), {"id": conta_id})
    return nova_sessao(engine, conta_id)


def redefinir_senha(engine: sa.Engine, conta_id: int) -> None:
    with engine.begin() as conn:
        conta = conn.execute(
            sa.text("UPDATE acesso.conta SET senha_hash = NULL WHERE id = :id RETURNING id"),
            {"id": conta_id},
        ).first()
        conn.execute(sa.text("DELETE FROM acesso.sessao WHERE conta_id = :id"), {"id": conta_id})
    if conta is None:
        raise SemAcesso(404, "Conta não encontrada.")


def exigir(a: Acesso, recurso: str) -> None:
    if recurso not in a.plano.recursos:
        raise SemAcesso(
            403,
            f"O plano {a.plano.codigo} não inclui {NOME_DO_RECURSO[recurso]}. Veja os planos em /.",
        )


def planos_publicos(engine: sa.Engine) -> list[dict]:
    with engine.connect() as conn:
        return [
            dict(p._mapping)
            for p in conn.execute(
                sa.text(
                    "SELECT codigo, nome, descricao, limite_por_minuto, limite_por_dia, "
                    "historico_dias, preco_mensal_centavos, preco_anual_centavos, recursos "
                    "FROM acesso.plano WHERE publico ORDER BY ordem"
                )
            )
        ]


def criar_conta(
    engine: sa.Engine,
    email: str,
    nome: str,
    plano: str,
    observacao: str | None,
    pago_ate: date | None = None,
) -> dict:
    with engine.begin() as conn:
        existe = conn.execute(
            sa.text("SELECT 1 FROM acesso.conta WHERE lower(email) = lower(:e)"), {"e": email}
        ).first()
        if existe:
            raise SemAcesso(409, "Já existe uma conta com esse e-mail.")
        if not conn.execute(
            sa.text("SELECT 1 FROM acesso.plano WHERE codigo = :p"), {"p": plano}
        ).first():
            raise SemAcesso(422, f"Plano desconhecido: {plano}.")
        conta = conn.execute(
            sa.text(
                "INSERT INTO acesso.conta (email, nome, plano, observacao, pago_ate) "
                "VALUES (:e, :n, :p, :o, :pago) "
                "RETURNING id, email, nome, plano, ativa, criada_em, pago_ate"
            ),
            {
                "e": email.strip(),
                "n": nome.strip(),
                "p": plano,
                "o": (observacao or "").strip() or None,
                "pago": pago_ate,
            },
        ).one()
    return dict(conta._mapping)


_CONTA_DO_EMAIL = sa.text(
    """
    SELECT c.id, c.ativa, c.pago_ate, p.preco_mensal_centavos IS NOT NULL AS plano_pago,
        EXISTS (
            SELECT 1 FROM acesso.assinatura s WHERE s.conta_id = c.id AND (
                s.situacao = 'ativa'
                OR (s.situacao = 'aguardando' AND s.criada_em > now() - :pendente)
            )
        ) AS aguardando
    FROM acesso.conta c JOIN acesso.plano p ON p.codigo = c.plano
    WHERE lower(c.email) = lower(:e)
    """
)


def conta_do_cadastro(engine: sa.Engine, email: str, nome: str, plano: str, senha: str) -> int:
    senha_hash = hash_da_senha(senha)
    with engine.begin() as conn:
        conta = conn.execute(
            _CONTA_DO_EMAIL, {"e": email, "pendente": CADASTRO_AGUARDANDO_PAGAMENTO}
        ).first()
        if conta is None:
            try:
                with conn.begin_nested():
                    return conn.execute(
                        sa.text(
                            "INSERT INTO acesso.conta (email, nome, plano, observacao, senha_hash) "
                            "VALUES (:e, :n, :p, 'cadastro pelo portal', :s) RETURNING id"
                        ),
                        {"e": email, "n": nome, "p": plano, "s": senha_hash},
                    ).scalar_one()
            except sa.exc.IntegrityError:
                raise SemAcesso(
                    409, "Esse e-mail acabou de ser cadastrado. Tente de novo."
                ) from None
        if not conta.ativa or not conta.plano_pago or conta.pago_ate is not None:
            raise SemAcesso(
                409,
                "Já existe uma conta com esse e-mail. Entre em Minha conta para assinar.",
            )
        if conta.aguardando:
            raise SemAcesso(
                409,
                "Esse e-mail tem uma assinatura aguardando pagamento. Use o link que recebeu, ou "
                "fale com o contato do portal.",
            )
        conn.execute(
            sa.text(
                "UPDATE acesso.chave SET revogada_em = now() "
                "WHERE conta_id = :id AND revogada_em IS NULL"
            ),
            {"id": conta.id},
        )
        conn.execute(sa.text("DELETE FROM acesso.sessao WHERE conta_id = :id"), {"id": conta.id})
        conn.execute(
            sa.text(
                "UPDATE acesso.conta SET nome = :n, plano = :p, senha_hash = :s WHERE id = :id"
            ),
            {"n": nome, "p": plano, "s": senha_hash, "id": conta.id},
        )
        return conta.id


def emitir_chave(engine: sa.Engine, conta_id: int, nome: str, por_dia: int | None = None) -> dict:
    texto, prefixo, hash_ = gerar_chave()
    with engine.begin() as conn:
        conta = conn.execute(
            sa.text(
                "SELECT c.ativa, p.chaves_maximas FROM acesso.conta c "
                "JOIN acesso.plano p ON p.codigo = c.plano WHERE c.id = :id"
            ),
            {"id": conta_id},
        ).first()
        if conta is None:
            raise SemAcesso(404, "Conta não encontrada.")
        if not conta.ativa:
            raise SemAcesso(409, "Conta desativada não recebe chave.")
        ativas = conn.execute(
            sa.text(
                "SELECT count(*) FROM acesso.chave WHERE conta_id = :id AND revogada_em IS NULL"
            ),
            {"id": conta_id},
        ).scalar_one()
        if ativas >= conta.chaves_maximas:
            raise SemAcesso(
                409, f"O plano permite {conta.chaves_maximas} chaves ativas: revogue uma antes."
            )
        if por_dia is not None:
            emitidas = conn.execute(
                sa.text(
                    "SELECT count(*) FROM acesso.chave "
                    "WHERE conta_id = :id AND criada_em > now() - interval '1 day'"
                ),
                {"id": conta_id},
            ).scalar_one()
            if emitidas >= por_dia:
                raise SemAcesso(429, f"No máximo {por_dia} chaves novas por dia.")
        conn.execute(
            sa.text(
                "INSERT INTO acesso.chave (conta_id, prefixo, hash, nome) VALUES (:c, :p, :h, :n)"
            ),
            {"c": conta_id, "p": prefixo, "h": hash_, "n": nome},
        )
    return {"chave": texto, "prefixo": prefixo, "nome": nome}


def revogar_chave(engine: sa.Engine, conta_id: int, prefixo: str) -> None:
    with engine.begin() as conn:
        revogada = conn.execute(
            sa.text(
                "UPDATE acesso.chave SET revogada_em = now() "
                "WHERE conta_id = :c AND prefixo = :p AND revogada_em IS NULL RETURNING id"
            ),
            {"c": conta_id, "p": prefixo},
        ).first()
    if revogada is None:
        raise SemAcesso(404, "Chave não encontrada nesta conta, ou já revogada.")


def remover_conta(engine: sa.Engine, conta_id: int) -> None:
    with engine.begin() as conn:
        conta = conn.execute(
            sa.text("SELECT ativa FROM acesso.conta WHERE id = :id FOR UPDATE"), {"id": conta_id}
        ).first()
        if conta is None:
            raise SemAcesso(404, "Conta não encontrada.")
        if conta.ativa:
            raise SemAcesso(409, "Desative a conta antes de removê-la.")
        for consulta in (
            "DELETE FROM acesso.uso_diario WHERE chave_id IN "
            "(SELECT id FROM acesso.chave WHERE conta_id = :id)",
            "DELETE FROM acesso.chave WHERE conta_id = :id",
            "DELETE FROM acesso.sessao WHERE conta_id = :id",
            "DELETE FROM acesso.pagamento WHERE assinatura_id IN "
            "(SELECT id FROM acesso.assinatura WHERE conta_id = :id)",
            "DELETE FROM acesso.assinatura WHERE conta_id = :id",
            "DELETE FROM acesso.conta WHERE id = :id",
        ):
            conn.execute(sa.text(consulta), {"id": conta_id})


def preparar_conta_de_fumaca(engine: sa.Engine, plano: str) -> int:
    with engine.begin() as conn:
        conta_id = conn.execute(
            sa.text(
                """
                INSERT INTO acesso.conta (email, nome, plano, observacao, pago_ate)
                VALUES (:e, :n, :p, :o, :pago)
                ON CONFLICT ((lower(email))) DO UPDATE
                    SET plano = excluded.plano, ativa = true, pago_ate = excluded.pago_ate
                RETURNING id
                """
            ),
            {
                "e": f"{plano}{DOMINIO_DA_FUMACA}",
                "n": f"Fumaça {plano}",
                "p": plano,
                "o": "Conta da fumaça do console: só tem chave enquanto a fumaça roda.",
                "pago": PAGO_ATE_DA_FUMACA,
            },
        ).scalar_one()
        conn.execute(
            sa.text(
                "UPDATE acesso.chave SET revogada_em = now() "
                "WHERE conta_id = :c AND revogada_em IS NULL"
            ),
            {"c": conta_id},
        )
    return conta_id


def resumo_da_conta(engine: sa.Engine, conta_id: int, dia: date | None = None) -> dict:
    with engine.connect() as conn:
        conta = conn.execute(
            sa.text(
                "SELECT c.id, c.email, c.nome, c.ativa, c.criada_em, c.pago_ate, c.observacao, "
                "p.codigo AS plano, p.nome AS plano_nome, p.limite_por_minuto, p.limite_por_dia, "
                "p.historico_dias, p.chaves_maximas, p.recursos, "
                "c.senha_hash IS NOT NULL AS tem_senha, "
                f"p.preco_mensal_centavos IS NOT NULL AS plano_pago, {_AGUARDANDO} "
                "FROM acesso.conta c JOIN acesso.plano p ON p.codigo = c.plano WHERE c.id = :id"
            ),
            {"id": conta_id},
        ).first()
        if conta is None:
            raise SemAcesso(404, "Conta não encontrada.")
        chaves = conn.execute(
            sa.text(
                """
                SELECT k.prefixo, k.nome, k.criada_em, k.revogada_em, k.ultimo_uso_em,
                    coalesce(u.requisicoes, 0) AS requisicoes_hoje
                FROM acesso.chave k
                LEFT JOIN acesso.uso_diario u ON u.chave_id = k.id AND u.dia = :dia
                WHERE k.conta_id = :id ORDER BY k.criada_em
                """
            ),
            {"id": conta_id, "dia": dia or hoje()},
        ).all()
        assinaturas = conn.execute(
            sa.text(
                "SELECT plano, ciclo, parcelas, situacao, criada_em, asaas_assinatura "
                "FROM acesso.assinatura "
                "WHERE conta_id = :id ORDER BY criada_em DESC, id DESC"
            ),
            {"id": conta_id},
        ).all()
    atual = next((s for s in assinaturas if s.situacao != "substituida"), None)
    resumo = {k: v for k, v in conta._mapping.items() if k != "aguardando"}
    return {
        **resumo,
        "situacao": _situacao(conta, dia or hoje()),
        "requisicoes_hoje": sum(k.requisicoes_hoje for k in chaves),
        "chaves": [dict(k._mapping) for k in chaves],
        "assinatura": None if atual is None else dict(atual._mapping),
        "cadastro_de_cobranca": bool(assinaturas),
    }


def listar_contas(engine: sa.Engine, dia: date | None = None) -> list[dict]:
    dia_de_hoje = dia or hoje()
    with engine.connect() as conn:
        linhas = conn.execute(
            sa.text(
                f"""
                WITH uso AS (
                    SELECT k.conta_id,
                        sum(u.requisicoes) FILTER (WHERE u.dia = :dia) AS hoje,
                        sum(u.requisicoes) AS trinta_dias
                    FROM acesso.uso_diario u JOIN acesso.chave k ON k.id = u.chave_id
                    WHERE u.dia > :desde GROUP BY k.conta_id
                ), chaves AS (
                    SELECT conta_id, count(*) FILTER (WHERE revogada_em IS NULL) AS ativas,
                        max(ultimo_uso_em) AS ultimo_uso_em
                    FROM acesso.chave GROUP BY conta_id
                )
                SELECT c.id, c.email, c.nome, c.plano, p.nome AS plano_nome, c.ativa, c.criada_em,
                    c.pago_ate, c.observacao, p.limite_por_dia, p.chaves_maximas,
                    c.senha_hash IS NOT NULL AS tem_senha,
                    p.preco_mensal_centavos IS NOT NULL AS plano_pago, {_AGUARDANDO},
                    coalesce(k.ativas, 0) AS chaves_ativas, k.ultimo_uso_em,
                    coalesce(u.hoje, 0) AS requisicoes_hoje,
                    coalesce(u.trinta_dias, 0) AS requisicoes_30_dias
                FROM acesso.conta c
                JOIN acesso.plano p ON p.codigo = c.plano
                LEFT JOIN chaves k ON k.conta_id = c.id
                LEFT JOIN uso u ON u.conta_id = c.id
                WHERE c.email NOT LIKE :fumaca
                ORDER BY c.id
                """
            ),
            {
                "dia": dia_de_hoje,
                "desde": dia_de_hoje - timedelta(days=30),
                "fumaca": f"%{DOMINIO_DA_FUMACA}",
            },
        ).all()
    return [
        {
            **{k: v for k, v in linha._mapping.items() if k != "aguardando"},
            "situacao": _situacao(linha, dia_de_hoje),
        }
        for linha in linhas
    ]


def alterar_conta(
    engine: sa.Engine,
    conta_id: int,
    plano: str | None,
    ativa: bool | None,
    pago_ate: date | None = None,
    *,
    mudar_pago_ate: bool = False,
    nome: str | None = None,
    observacao: str | None = None,
    mudar_observacao: bool = False,
) -> dict:
    with engine.begin() as conn:
        if (
            plano is not None
            and not conn.execute(
                sa.text("SELECT 1 FROM acesso.plano WHERE codigo = :p"), {"p": plano}
            ).first()
        ):
            raise SemAcesso(422, f"Plano desconhecido: {plano}.")
        conta = conn.execute(
            sa.text(
                "UPDATE acesso.conta SET plano = coalesce(:p, plano), ativa = coalesce(:a, ativa), "
                "nome = coalesce(:n, nome), "
                "pago_ate = CASE WHEN :mudar_pago THEN CAST(:pago AS date) "
                "ELSE coalesce(CAST(:pago AS date), pago_ate) END, "
                "observacao = CASE WHEN :mudar_obs THEN :o ELSE observacao END "
                "WHERE id = :id "
                "RETURNING id, email, nome, plano, ativa, criada_em, pago_ate, observacao"
            ),
            {
                "p": plano,
                "a": ativa,
                "n": nome.strip() if nome else None,
                "pago": pago_ate,
                "mudar_pago": mudar_pago_ate,
                "o": (observacao or "").strip() or None,
                "mudar_obs": mudar_observacao,
                "id": conta_id,
            },
        ).first()
    if conta is None:
        raise SemAcesso(404, "Conta não encontrada.")
    return dict(conta._mapping)


def planos(engine: sa.Engine) -> list[dict]:
    with engine.connect() as conn:
        return [
            dict(p._mapping)
            for p in conn.execute(
                sa.text("SELECT * FROM acesso.plano ORDER BY publico, ordem, limite_por_dia")
            )
        ]


def uso_por_dia(engine: sa.Engine, dias: int = 30, conta_id: int | None = None) -> list[dict]:
    with engine.connect() as conn:
        linhas = conn.execute(
            sa.text(
                """
                SELECT u.dia, sum(u.requisicoes) AS requisicoes, count(DISTINCT k.conta_id) AS contas
                FROM acesso.uso_diario u JOIN acesso.chave k ON k.id = u.chave_id
                JOIN acesso.conta c ON c.id = k.conta_id
                WHERE u.dia > :desde AND (CAST(:conta AS bigint) IS NULL OR k.conta_id = :conta)
                  AND c.email NOT LIKE :fumaca
                GROUP BY u.dia ORDER BY u.dia
                """
            ),
            {
                "desde": hoje() - timedelta(days=dias),
                "conta": conta_id,
                "fumaca": f"%{DOMINIO_DA_FUMACA}",
            },
        ).all()
    return [dict(linha._mapping) for linha in linhas]
