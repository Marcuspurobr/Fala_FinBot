"""Senha e sessão de login.

A sessão fica só no Redis, com tempo de expiração: depois do login, as próximas requisições
leem a sessão de lá, sem consultar o MongoDB.
"""
import json
import secrets

import bcrypt
import redis

EXPIRA_EM_SEGUNDOS = 30 * 60  # 30 minutos


def senha_confere(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:  # hash em formato inválido
        return False


def _chave(token: str) -> str:
    return f"sessao:{token}"


def criar_sessao(r: redis.Redis, usuario: dict) -> str:
    token = secrets.token_urlsafe(32)
    dados = {
        "usuarioId": str(usuario["_id"]),
        "empresaId": str(usuario["empresaId"]),
        "nome": usuario["nome"],
    }
    r.setex(_chave(token), EXPIRA_EM_SEGUNDOS, json.dumps(dados))
    return token


def ler_sessao(r: redis.Redis, token: str) -> dict | None:
    bruto = r.get(_chave(token))
    if bruto is None:
        return None
    return {**json.loads(bruto), "expiraEmSegundos": max(r.ttl(_chave(token)), 0)}


def apagar_sessao(r: redis.Redis, token: str) -> None:
    r.delete(_chave(token))
