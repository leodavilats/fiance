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
_BRT = ZoneInfo("America/Sao_Paulo")
TOLERANCIA_DE_PAGAMENTO = timedelta(days=3)
NOME_DO_RECURSO = {
    "serie": "a série ajustada",
    "ponto_no_tempo": "o balanço como se sabia na data (sabido_em)",
    "informes": "o informe mensal de FII",
    "exportacao": "a exportação da base",
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


# Janela fixa por minuto na memória do processo: com mais de uma réplica, cada uma conta a sua.
class LimitePorMinuto:
    def __init__(self, relogio=time.monotonic):
        self._relogio = relogio
        self._contagens: dict[int, tuple[int, int]] = {}
        self._trava = threading.Lock()

    def registrar(self, chave_id: int, limite: int) -> int | None:
        agora = self._relogio()
        minuto = int(agora // 60)
        with self._trava:
            janela, contagem = self._contagens.get(chave_id, (minuto, 0))
            if janela != minuto:
                janela, contagem = minuto, 0
            if contagem >= limite:
                return int(60 - agora % 60) + 1
            self._contagens[chave_id] = (janela, contagem + 1)
        return None


class TentativasDeAdministracao:
    def __init__(self, maximo: int = 10, janela: float = 900.0, relogio=time.monotonic):
        self._maximo, self._janela, self._relogio = maximo, janela, relogio
        self._falhas: dict[str, list[float]] = {}
        self._trava = threading.Lock()

    def bloqueado(self, origem: str) -> bool:
        agora = self._relogio()
        with self._trava:
            recentes = [t for t in self._falhas.get(origem, []) if agora - t < self._janela]
            self._falhas[origem] = recentes
            return len(recentes) >= self._maximo

    def falhou(self, origem: str) -> None:
        with self._trava:
            self._falhas.setdefault(origem, []).append(self._relogio())


_CHAVE_VALIDA = sa.text(
    """
    SELECT k.id AS chave_id, k.prefixo, c.id AS conta_id, c.pago_ate, p.codigo,
        p.limite_por_minuto, p.limite_por_dia, p.historico_dias, p.chaves_maximas, p.recursos,
        p.preco_mensal_centavos
    FROM acesso.chave k
    JOIN acesso.conta c ON c.id = k.conta_id
    JOIN acesso.plano p ON p.codigo = c.plano
    WHERE k.hash = :hash AND k.revogada_em IS NULL AND c.ativa
    """
)

_CONTAR_USO = sa.text(
    """
    INSERT INTO acesso.uso_diario (chave_id, dia, requisicoes) VALUES (:chave, :dia, 1)
    ON CONFLICT (chave_id, dia) DO UPDATE SET requisicoes = acesso.uso_diario.requisicoes + 1
    RETURNING requisicoes
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
        if plano.pago and (
            linha.pago_ate is None or linha.pago_ate + TOLERANCIA_DE_PAGAMENTO < dia_de_hoje
        ):
            raise SemAcesso(402, "A assinatura da conta está vencida ou não foi paga.")
        espera = por_minuto.registrar(linha.chave_id, plano.limite_por_minuto)
        if espera is not None:
            raise SemAcesso(429, "Limite por minuto atingido.", tentar_em=espera)
        usadas = conn.execute(
            _CONTAR_USO, {"chave": linha.chave_id, "dia": dia_de_hoje}
        ).scalar_one()
        conn.execute(
            sa.text("UPDATE acesso.chave SET ultimo_uso_em = now() WHERE id = :id"),
            {"id": linha.chave_id},
        )
    if usadas > plano.limite_por_dia:
        raise SemAcesso(429, "Limite do dia atingido. Ele volta à meia-noite de Brasília.")
    return Acesso(linha.conta_id, linha.chave_id, linha.prefixo, plano, usadas)


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
    engine: sa.Engine, email: str, nome: str, plano: str, observacao: str | None
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
                "INSERT INTO acesso.conta (email, nome, plano, observacao) "
                "VALUES (:e, :n, :p, :o) RETURNING id, email, nome, plano, ativa, criada_em"
            ),
            {"e": email.strip(), "n": nome.strip(), "p": plano, "o": observacao},
        ).one()
    return dict(conta._mapping)


def emitir_chave(engine: sa.Engine, conta_id: int, nome: str) -> dict:
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


def resumo_da_conta(engine: sa.Engine, conta_id: int, dia: date | None = None) -> dict:
    with engine.connect() as conn:
        conta = conn.execute(
            sa.text(
                "SELECT c.id, c.email, c.nome, c.ativa, c.criada_em, c.pago_ate, "
                "p.codigo AS plano, p.limite_por_minuto, p.limite_por_dia, p.historico_dias, "
                "p.chaves_maximas, p.recursos "
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
    return {**dict(conta._mapping), "chaves": [dict(k._mapping) for k in chaves]}


def listar_contas(engine: sa.Engine, dia: date | None = None) -> list[dict]:
    with engine.connect() as conn:
        linhas = conn.execute(
            sa.text(
                """
                SELECT c.id, c.email, c.nome, c.plano, c.ativa, c.criada_em, c.pago_ate,
                    count(k.id) FILTER (WHERE k.revogada_em IS NULL) AS chaves_ativas,
                    coalesce(sum(u.requisicoes), 0) AS requisicoes_hoje
                FROM acesso.conta c
                LEFT JOIN acesso.chave k ON k.conta_id = c.id
                LEFT JOIN acesso.uso_diario u ON u.chave_id = k.id AND u.dia = :dia
                GROUP BY c.id ORDER BY c.id
                """
            ),
            {"dia": dia or hoje()},
        ).all()
    return [dict(linha._mapping) for linha in linhas]


def alterar_conta(
    engine: sa.Engine,
    conta_id: int,
    plano: str | None,
    ativa: bool | None,
    pago_ate: date | None = None,
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
                "pago_ate = coalesce(CAST(:pago AS date), pago_ate) "
                "WHERE id = :id RETURNING id, email, nome, plano, ativa, criada_em, pago_ate"
            ),
            {"p": plano, "a": ativa, "pago": pago_ate, "id": conta_id},
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


def uso_por_dia(engine: sa.Engine, dias: int = 30) -> list[dict]:
    with engine.connect() as conn:
        linhas = conn.execute(
            sa.text(
                """
                SELECT u.dia, sum(u.requisicoes) AS requisicoes, count(DISTINCT k.conta_id) AS contas
                FROM acesso.uso_diario u JOIN acesso.chave k ON k.id = u.chave_id
                WHERE u.dia > :desde GROUP BY u.dia ORDER BY u.dia
                """
            ),
            {"desde": hoje() - timedelta(days=dias)},
        ).all()
    return [dict(linha._mapping) for linha in linhas]
