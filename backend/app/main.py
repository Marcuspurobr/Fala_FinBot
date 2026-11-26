"""API do Fala_FinBot.

    uvicorn app.main:app --reload

A documentação interativa fica em http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated

import redis
from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from pymongo.database import Database

from . import auth, bloom, estatisticas, queries
from .db import get_db
from .redis_client import get_redis


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Ao iniciar: cria o Bloom Filter (se preciso) e carrega nele os e-mails já cadastrados
    bloom.preparar_filtro(get_redis(), get_db())
    yield


app = FastAPI(
    title="Fala_FinBot API",
    description="Agregações do MongoDB para o painel financeiro, com login em cache no Redis. "
    "Os valores vêm em centavos.",
    lifespan=lifespan,
)

Db = Annotated[Database, Depends(get_db)]
Redis = Annotated[redis.Redis, Depends(get_redis)]

EmpresaId = Annotated[
    str | None,
    Query(alias="empresaId", description="Filtra por empresa. Sem ele, considera todas."),
]


def _empresa(empresa_id: str | None) -> ObjectId | None:
    if empresa_id is None:
        return None
    if not ObjectId.is_valid(empresa_id):
        raise HTTPException(status_code=422, detail="empresaId inválido: use um ObjectId de 24 caracteres.")
    return ObjectId(empresa_id)


@app.get("/health")
def health(db: Db, r: Redis):
    db.command("ping")
    r.ping()
    return {"status": "ok", "banco": db.name, "redis": "ok"}


# ---------- Agregações ----------
@app.get("/api/funcionalidade1", summary="Despesas por categoria")
def funcionalidade1(db: Db, empresa_id: EmpresaId = None):
    """Quanto foi gasto em cada categoria, da maior despesa para a menor."""
    return queries.despesas_por_categoria(db, _empresa(empresa_id))


@app.get("/api/funcionalidade2", summary="Resumo mensal")
def funcionalidade2(db: Db, empresa_id: EmpresaId = None):
    """Receitas, despesas e saldo (receitas menos despesas) de cada mês."""
    return queries.resumo_mensal(db, _empresa(empresa_id))


# ---------- Login (Bloom Filter + sessão no Redis) ----------
class LoginIn(BaseModel):
    email: str
    senha: str


CREDENCIAIS_INVALIDAS = HTTPException(status_code=401, detail="e-mail ou senha inválidos")


@app.post("/api/login", summary="Login")
def login(dados: LoginIn, db: Db, r: Redis):
    """Confere e-mail e senha e cria a sessão no Redis.

    1. O Bloom Filter responde primeiro: se o e-mail "não está", recusa sem consultar o MongoDB.
    2. Se "provavelmente está", o MongoDB confirma (o filtro pode ter dado um falso positivo).
    3. Com a senha certa, cria a sessão no Redis com tempo de expiração.
    4. Anota o usuário na estatística do dia (HyperLogLog).
    """
    if not bloom.provavelmente_existe(r, dados.email):
        raise CREDENCIAIS_INVALIDAS

    usuario = db.usuarios.find_one({"email": bloom.normalizar(dados.email)})
    if usuario is None or not auth.senha_confere(dados.senha, usuario["senhaHash"]):
        raise CREDENCIAIS_INVALIDAS

    token = auth.criar_sessao(r, usuario)
    estatisticas.registrar_acesso(r, str(usuario["_id"]))
    return {"token": token, "expiraEmSegundos": auth.EXPIRA_EM_SEGUNDOS}


# Faz o /docs mostrar o botão "Authorize" e enviar o cabeçalho Authorization: Bearer <token>
bearer = HTTPBearer(auto_error=False, description="Token devolvido pelo login")


def _token(credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> str:
    if credenciais is None:
        raise HTTPException(status_code=401, detail="envie o cabeçalho Authorization: Bearer <token>")
    return credenciais.credentials


Token = Annotated[str, Depends(_token)]


@app.get("/api/me", summary="Usuário da sessão")
def me(r: Redis, token: Token):
    """Devolve os dados da sessão, lidos direto do Redis (sem consultar o MongoDB)."""
    sessao = auth.ler_sessao(r, token)
    if sessao is None:
        raise HTTPException(status_code=401, detail="sessão inválida ou expirada")
    return sessao


@app.post("/api/logout", summary="Logout")
def logout(r: Redis, token: Token):
    """Apaga a sessão do Redis."""
    auth.apagar_sessao(r, token)
    return {"status": "sessão encerrada"}


# ---------- Estatísticas de uso (HyperLogLog) ----------
@app.get("/api/estatisticas", summary="Usuários únicos por dia")
def estatisticas_de_uso(
    r: Redis,
    dia: Annotated[date | None, Query(alias="data", description="AAAA-MM-DD. Sem ela, considera hoje.")] = None,
):
    """Quantos usuários diferentes fizeram login no dia (contagem aproximada)."""
    dia = dia or date.today()
    return {
        "data": dia.isoformat(),
        "usuariosUnicosEstimados": estatisticas.usuarios_unicos(r, dia),
    }


@app.get("/api/bloom/verificar", summary="Pergunta ao Bloom Filter (demonstração)")
def verificar_email(r: Redis, email: str):
    """Só para demonstrar o filtro: "não existe" é certeza; "provavelmente existe" pode ser falso positivo."""
    return {
        "email": email,
        "resposta": "provavelmente existe" if bloom.provavelmente_existe(r, email) else "não existe",
    }
