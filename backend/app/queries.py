"""As duas agregações do projeto (as mesmas views criadas no Atlas).

Os valores estão guardados em centavos. É nesta camada que o cache com Redis será encaixado
na próxima entrega: as rotas chamam estas funções e não precisam saber de onde vem o resultado.
"""
from bson import ObjectId
from pymongo.database import Database


def _filtro_empresa(empresa_id: ObjectId | None) -> list[dict]:
    """Sem empresa: considera todas (igual às views do Atlas). Com empresa: só os dados dela."""
    return [{"$match": {"empresaId": empresa_id}}] if empresa_id else []


def despesas_por_categoria(db: Database, empresa_id: ObjectId | None = None) -> list[dict]:
    """Funcionalidade 1: quanto foi gasto em cada categoria, da maior despesa para a menor."""
    pipeline = [
        *_filtro_empresa(empresa_id),
        {"$match": {"tipo": "despesa"}},
        {"$group": {"_id": "$categoria", "total": {"$sum": "$valorCentavos"}}},
        {"$sort": {"total": -1}},
    ]
    return [
        {"categoria": linha["_id"], "totalCentavos": linha["total"]}
        for linha in db.lancamentos.aggregate(pipeline)
    ]


def resumo_mensal(db: Database, empresa_id: ObjectId | None = None) -> list[dict]:
    """Funcionalidade 2: receitas, despesas e saldo de cada mês, do mais antigo para o mais recente."""
    pipeline = [
        *_filtro_empresa(empresa_id),
        {
            "$group": {
                "_id": {"$substrBytes": ["$data", 0, 7]},
                "receitas": {
                    "$sum": {"$cond": [{"$eq": ["$tipo", "receita"]}, "$valorCentavos", 0]}
                },
                "despesas": {
                    "$sum": {"$cond": [{"$eq": ["$tipo", "despesa"]}, "$valorCentavos", 0]}
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "mes": "$_id",
                "receitas": 1,
                "despesas": 1,
                "saldo": {"$subtract": ["$receitas", "$despesas"]},
            }
        },
        {"$sort": {"mes": 1}},
    ]
    return [
        {
            "mes": linha["mes"],
            "receitasCentavos": linha["receitas"],
            "despesasCentavos": linha["despesas"],
            "saldoCentavos": linha["saldo"],
        }
        for linha in db.lancamentos.aggregate(pipeline)
    ]
