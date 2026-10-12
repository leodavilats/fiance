from __future__ import annotations

import base64
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from api import arquivos, banco, consultas
from api.config import Configuracao, carregar

_LIVRES = {"/saude"}


def criar(config: Configuracao | None = None, engine=None) -> FastAPI:
    config = config or carregar()
    engine = engine or banco.criar(config.database_url)
    app = FastAPI(title="trend", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def _senha(request: Request, seguir):
        if request.url.path in _LIVRES or _autorizado(request, config):
            return await seguir(request)
        return Response(
            status_code=401, headers={"WWW-Authenticate": 'Basic realm="trend", charset="UTF-8"'}
        )

    @app.get("/saude")
    def saude() -> dict:
        return {"ok": True}

    @app.get("/api/coleta")
    def coleta() -> dict:
        with engine.connect() as conn:
            return consultas.coleta(conn)

    @app.get("/api/papeis")
    def papeis() -> list[dict]:
        with engine.connect() as conn:
            return consultas.papeis(conn)

    @app.get("/api/papeis/{cnpj}/{classe}")
    def papel(cnpj: str, classe: str) -> dict:
        with engine.connect() as conn:
            dados = consultas.papel(conn, cnpj, classe)
        if dados is None:
            raise HTTPException(404, "Papel não encontrado.")
        return dados

    @app.get("/api/pesquisa")
    def pesquisa() -> dict:
        return {"execucoes": arquivos.registro(config.pesquisa)}

    @app.get("/api/pesquisa/curva/{hipotese}/{assinatura}/{periodo}")
    def curva(hipotese: str, assinatura: str, periodo: str) -> dict:
        dados = arquivos.curva(config.pesquisa, hipotese, assinatura, periodo)
        if dados is None:
            raise HTTPException(404, "Curva não encontrada.")
        return dados

    @app.get("/api/documentos")
    def documentos() -> list[dict]:
        return arquivos.documentos(config.docs)

    @app.get("/api/documentos/{nome:path}")
    def documento(nome: str) -> JSONResponse:
        texto = arquivos.documento(config.docs, nome)
        if texto is None:
            raise HTTPException(404, "Documento não encontrado.")
        return JSONResponse({"nome": nome, "texto": texto})

    @app.get("/{caminho:path}")
    def front(caminho: str) -> FileResponse:
        if caminho.startswith("api/"):
            raise HTTPException(404)
        return FileResponse(_arquivo_do_front(config.front, caminho))

    return app


def _autorizado(request: Request, config: Configuracao) -> bool:
    cabecalho = request.headers.get("authorization", "")
    if not cabecalho.startswith("Basic "):
        return False
    try:
        usuario, _, senha = base64.b64decode(cabecalho[6:]).decode().partition(":")
    except (ValueError, UnicodeDecodeError):
        return False
    return secrets.compare_digest(usuario, config.usuario) & secrets.compare_digest(
        senha, config.senha
    )


def _arquivo_do_front(raiz: Path, caminho: str) -> Path:
    alvo = (raiz / caminho).resolve()
    if caminho and alvo.is_file() and raiz.resolve() in alvo.parents:
        return alvo
    indice = raiz / "index.html"
    if not indice.exists():
        raise HTTPException(503, "O front não foi compilado.")
    return indice
