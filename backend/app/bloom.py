"""Bloom Filter com os e-mails cadastrados.

Serve para o login recusar na hora um e-mail que não existe, sem consultar o MongoDB:
  - "não está"            -> certeza: o e-mail nunca foi cadastrado
  - "provavelmente está"  -> pode ser falso positivo, então o MongoDB confere
O filtro não esquece ninguém (não há falso negativo), mas também não permite remover um item.
"""
import redis
from pymongo.database import Database

CHAVE = "bf:emails"
TAXA_DE_ERRO = 0.01  # 1% de falsos positivos
CAPACIDADE = 1000  # quantos e-mails o filtro comporta mantendo essa taxa


def normalizar(email: str) -> str:
    return email.strip().lower()


def preparar_filtro(r: redis.Redis, db: Database) -> int:
    """Cria o filtro (se ainda não existir) e carrega nele os e-mails de `usuarios`.

    Pode rodar quantas vezes quiser: adicionar de novo um e-mail que já está no filtro não muda nada.
    """
    try:
        r.bf().reserve(CHAVE, TAXA_DE_ERRO, CAPACIDADE)
    except redis.ResponseError as erro:
        if "exists" not in str(erro).lower():
            raise
    emails = [normalizar(u["email"]) for u in db.usuarios.find({}, {"email": 1})]
    if emails:
        r.bf().madd(CHAVE, *emails)
    return len(emails)


def adicionar_email(r: redis.Redis, email: str) -> None:
    r.bf().add(CHAVE, normalizar(email))


def provavelmente_existe(r: redis.Redis, email: str) -> bool:
    return bool(r.bf().exists(CHAVE, normalizar(email)))
