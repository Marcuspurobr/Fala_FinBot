"""Lê a connection string do MongoDB do arquivo .env.

O nome do banco vem dentro da própria connection string (ex.: ...mongodb.net/finbot).
"""
import os
import sys
from pathlib import Path

import dns.resolver
from dotenv import load_dotenv

# O .env fica na pasta backend/, ao lado de requirements.txt
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Em algumas redes (empresa/VPN) o DNS local recusa a consulta SRV que o endereço
# "mongodb+srv://" do Atlas precisa. Usar DNS públicos primeiro evita esse erro.
_resolver = dns.resolver.Resolver(configure=True)
_resolver.nameservers = ["8.8.8.8", "1.1.1.1", *_resolver.nameservers]
dns.resolver.default_resolver = _resolver


def require_mongo_uri() -> str:
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        sys.exit("MONGODB_URI não configurada no arquivo backend/.env.")
    return uri


def require_redis_url() -> str:
    url = os.environ.get("REDIS_URL")
    if not url:
        sys.exit("REDIS_URL não configurada no arquivo backend/.env.")
    return url
