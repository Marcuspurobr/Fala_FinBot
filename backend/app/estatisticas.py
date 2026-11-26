"""Estatística de uso com HyperLogLog: quantos usuários diferentes entraram em cada dia.

O HyperLogLog é uma estrutura probabilística que conta itens distintos sem guardar a lista deles.
Ele ocupa no máximo uns 12 KB por chave, com qualquer quantidade de usuários, e em troca a
contagem é aproximada (erro típico perto de 1%).
"""
from datetime import date

import redis


def _chave(dia: date) -> str:
    return f"stats:usuarios-unicos:{dia.isoformat()}"  # uma chave por dia


def registrar_acesso(r: redis.Redis, usuario_id: str, dia: date | None = None) -> None:
    """Anota que o usuário entrou no dia. Entrar várias vezes no mesmo dia conta uma vez só."""
    r.pfadd(_chave(dia or date.today()), usuario_id)


def usuarios_unicos(r: redis.Redis, dia: date | None = None) -> int:
    """Quantidade estimada de usuários diferentes que entraram no dia (0 se ninguém entrou)."""
    return r.pfcount(_chave(dia or date.today()))
