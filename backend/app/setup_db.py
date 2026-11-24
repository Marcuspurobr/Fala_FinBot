"""Cria o banco "finbot", as 3 coleções (com validação e índices) e insere os documentos de exemplo.

    python -m app.setup_db            -> cria o que falta; coleções que já têm dados não são mexidas
    python -m app.setup_db --reset    -> apaga as 3 coleções e cria tudo de novo
"""
import sys

from pymongo.database import Database

from .db import get_db
from .schemas import COLLECTIONS
from .seed import build_seed_data


def setup_database(db: Database, reset: bool = False) -> list[dict]:
    existing = set(db.list_collection_names())

    if reset:
        for c in COLLECTIONS:
            if c["name"] in existing:
                db.drop_collection(c["name"])
        existing.clear()

    # 1) Coleções + regras de validação + índices
    for c in COLLECTIONS:
        if c["name"] not in existing:
            db.create_collection(
                c["name"],
                validator=c["validator"],
                validationLevel="strict",  # vale para inserir e para alterar
                validationAction="error",  # documento fora da regra é recusado
            )
        db[c["name"]].create_indexes(c["indexes"])

    # 2) Documentos de exemplo (só em coleções vazias).
    # A ordem importa só para leitura: empresas -> usuários -> lançamentos
    seed = build_seed_data()
    summary = []
    for c in COLLECTIONS:
        collection = db[c["name"]]
        if collection.estimated_document_count() == 0:
            collection.insert_many(seed[c["name"]])
        summary.append({"colecao": c["name"], "documentos": collection.count_documents({})})
    return summary


def main() -> None:
    reset = "--reset" in sys.argv
    db = get_db()
    print(f'Conectado. Preparando o banco "{db.name}"{" (reset)" if reset else ""}...')
    for linha in setup_database(db, reset=reset):
        print(f'  {linha["colecao"]}: {linha["documentos"]} documentos')
    print("Pronto! Confira no Atlas em Database -> Browse Collections.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001
        sys.exit(f"Falhou: {error}")
