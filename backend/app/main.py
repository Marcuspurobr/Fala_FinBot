"""API do Fala_FinBot.

    uvicorn app.main:app --reload

A documentação interativa fica em http://localhost:8000/docs
"""
from typing import Annotated

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, Query
from pymongo.database import Database

from . import queries
from .db import get_db

app = FastAPI(
    title="Fala_FinBot API",
    description="Agregações do MongoDB para o painel financeiro. Os valores vêm em centavos.",
)

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
def health(db: Annotated[Database, Depends(get_db)]):
    db.command("ping")
    return {"status": "ok", "banco": db.name}


@app.get("/api/funcionalidade1", summary="Despesas por categoria")
def funcionalidade1(db: Annotated[Database, Depends(get_db)], empresa_id: EmpresaId = None):
    """Quanto foi gasto em cada categoria, da maior despesa para a menor."""
    return queries.despesas_por_categoria(db, _empresa(empresa_id))


@app.get("/api/funcionalidade2", summary="Resumo mensal")
def funcionalidade2(db: Annotated[Database, Depends(get_db)], empresa_id: EmpresaId = None):
    """Receitas, despesas e saldo (receitas menos despesas) de cada mês."""
    return queries.resumo_mensal(db, _empresa(empresa_id))
