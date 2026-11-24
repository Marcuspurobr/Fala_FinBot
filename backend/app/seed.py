"""Documentos de exemplo: 2 empresas fictícias, cada uma com 1 usuário, e lançamentos de agosto a
novembro de 2026 (os que vieram do chat carregam a mensagem original embutida).
Todos os dados (empresas, e-mails, IDs de chat, valores) são inventados.
"""
from datetime import datetime, timezone

from bson import ObjectId


def at(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)


def reais(value: float) -> int:
    """R$ 180,00 -> 18000 centavos."""
    return round(value * 100)


# Hash de exemplo (parece um bcrypt, mas não é de nenhuma senha real)
FAKE_HASH = "$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ0123456"

# Cada linha: (data, tipo, categoria, descrição, valor em reais)
# Fica de fora o que foi lançado pelo chat (vem mais abaixo, com a mensagem embutida).
# O mês de novembro vai só até o dia 4.
PADARIA = [
    ("2026-08-05", "despesa", "Farinha", "Compra de farinha de trigo", 2100),
    ("2026-08-10", "despesa", "Aluguel", "Aluguel do ponto", 3500),
    ("2026-08-12", "despesa", "Energia", "Conta de energia", 1620),
    ("2026-08-31", "receita", "Vendas", "Vendas da semana no balcão", 11800),
    ("2026-09-05", "despesa", "Farinha", "Compra de farinha de trigo", 2250),
    ("2026-09-10", "despesa", "Aluguel", "Aluguel do ponto", 3500),
    ("2026-09-12", "despesa", "Gás", "Botijões de gás", 780),
    ("2026-09-30", "receita", "Vendas", "Vendas do mês no balcão", 13200),
    ("2026-10-10", "despesa", "Aluguel", "Aluguel do ponto", 3500),
    ("2026-10-31", "receita", "Vendas", "Vendas do mês no balcão", 14500),
]

MODAS = [
    ("2026-08-08", "despesa", "Fornecedores", "Pedido de coleção de verão", 9800),
    ("2026-08-10", "despesa", "Aluguel", "Aluguel da loja", 4200),
    ("2026-08-31", "receita", "Vendas", "Vendas do mês", 21500),
    ("2026-09-08", "despesa", "Fornecedores", "Reposição de estoque", 8700),
    ("2026-09-10", "despesa", "Aluguel", "Aluguel da loja", 4200),
    ("2026-09-18", "despesa", "Marketing", "Anúncios no Instagram", 600),
    ("2026-09-30", "receita", "Vendas", "Vendas do mês", 24300),
    ("2026-10-08", "despesa", "Fornecedores", "Pedido de coleção de primavera", 11200),
    ("2026-10-10", "despesa", "Aluguel", "Aluguel da loja", 4200),
    ("2026-10-31", "receita", "Vendas", "Vendas do mês", 27800),
    ("2026-11-02", "despesa", "Fornecedores", "Compra de vitrines", 3600),
]


def _lancamento_do_site(empresa_id, linha):
    data, tipo, categoria, descricao, valor = linha
    return {
        "empresaId": empresa_id,
        "tipo": tipo,
        "valorCentavos": reais(valor),
        "categoria": categoria,
        "descricao": descricao,
        "data": data,
        "origem": "site",
        "criadoEm": at(f"{data}T12:00:00Z"),
    }


def _lancamento_do_chat(
    *, empresa_id, usuario_id, tipo, valor, categoria, descricao, data, texto, recebida_em,
    ia_valor, ia_categoria, ia_data, confianca, status, criado_em, **extras,
):
    """Lançamento que veio do chat: a mensagem original e a interpretação da IA ficam embutidas."""
    return {
        "empresaId": empresa_id,
        "tipo": tipo,
        "valorCentavos": reais(valor),
        "categoria": categoria,
        "descricao": descricao,
        "data": data,
        "origem": "mensagem",
        "mensagem": {
            "usuarioId": usuario_id,
            "texto": texto,
            "recebidaEm": at(recebida_em),
            "interpretacao": {
                "tipo": tipo,
                "valorCentavos": reais(ia_valor),
                "categoria": ia_categoria,
                "data": ia_data,
                "confianca": confianca,
            },
            "status": status,
        },
        "criadoEm": at(criado_em),
        **extras,
    }


def build_seed_data() -> dict[str, list[dict]]:
    # ---------- Empresas ----------
    padaria = ObjectId()
    modas = ObjectId()

    empresas = [
        {
            "_id": padaria,
            "nome": "Padaria Pão Quente",
            "segmento": "alimentacao",
            "categorias": [
                {"nome": "Vendas", "tipo": "receita"},
                {"nome": "Encomendas", "tipo": "receita"},
                {"nome": "Farinha", "tipo": "despesa"},
                {"nome": "Gás", "tipo": "despesa"},
                {"nome": "Energia", "tipo": "despesa"},
                {"nome": "Aluguel", "tipo": "despesa"},
                {"nome": "Internet", "tipo": "despesa"},
            ],
            "criadaEm": at("2026-08-01T09:00:00Z"),
        },
        {
            "_id": modas,
            "nome": "Boutique Estação",
            "segmento": "varejo",
            "categorias": [
                {"nome": "Vendas", "tipo": "receita"},
                {"nome": "Fornecedores", "tipo": "despesa"},
                {"nome": "Marketing", "tipo": "despesa"},
                {"nome": "Aluguel", "tipo": "despesa"},
                {"nome": "Equipamentos", "tipo": "despesa"},
            ],
            "criadaEm": at("2026-08-03T14:00:00Z"),
        },
    ]

    # ---------- Usuários ----------
    maria = ObjectId()
    carlos = ObjectId()

    usuarios = [
        {
            "_id": maria,
            "empresaId": padaria,
            "nome": "Maria Souza",
            "email": "maria@paoquente.example",
            "senhaHash": FAKE_HASH,
            "canalMensagem": {"tipo": "telegram", "id": "100000001"},
            "criadoEm": at("2026-08-01T09:05:00Z"),
        },
        {
            "_id": carlos,
            "empresaId": modas,
            "nome": "Carlos Lima",
            "email": "carlos@estacao.example",
            "senhaHash": FAKE_HASH,
            "canalMensagem": {"tipo": "whatsapp", "id": "+5534999990001"},
            "criadoEm": at("2026-08-03T14:10:00Z"),
        },
    ]

    # ---------- Lançamentos ----------
    # Lançamentos feitos pelo site
    lancamentos = [_lancamento_do_site(padaria, l) for l in PADARIA]
    lancamentos += [_lancamento_do_site(modas, l) for l in MODAS]

    # Lançamentos que vieram do chat (a mensagem original fica embutida no campo "mensagem")
    lancamentos += [
        _lancamento_do_chat(
            empresa_id=padaria, usuario_id=maria, tipo="despesa", valor=820, categoria="Gás",
            descricao="2 botijões de gás", data="2026-10-12",
            texto="comprei 2 botijões de gás, 820", recebida_em="2026-10-12T13:10:00Z",
            ia_valor=820, ia_categoria="Gás", ia_data="2026-10-12", confianca=0.91,
            status="confirmada", criado_em="2026-10-12T13:11:00Z",
        ),
        _lancamento_do_chat(
            empresa_id=padaria, usuario_id=maria, tipo="despesa",
            valor=2350,  # valor corrigido pelo dono (a IA entendeu 2.400)
            categoria="Farinha", descricao="Compra de farinha de trigo", data="2026-10-05",
            texto="farinha 2400 ontem", recebida_em="2026-10-06T12:00:00Z",
            ia_valor=2400, ia_categoria="Farinha", ia_data="2026-10-05", confianca=0.82,
            status="corrigida", criado_em="2026-10-06T12:02:00Z",
            comprovante={
                "nomeArquivo": "nota-farinha-out.pdf",
                "url": "https://exemplo.example/comprovantes/nota-farinha-out.pdf",
            },
        ),
        _lancamento_do_chat(
            empresa_id=padaria, usuario_id=maria, tipo="receita", valor=950, categoria="Encomendas",
            descricao="Bolos de encomenda", data="2026-11-03",
            texto="vendi 950 de bolos de encomenda hoje", recebida_em="2026-11-03T20:30:00Z",
            ia_valor=950, ia_categoria="Encomendas", ia_data="2026-11-03", confianca=0.97,
            status="automatica", criado_em="2026-11-03T20:30:05Z",
            tags=["evento"],
        ),
        _lancamento_do_chat(
            empresa_id=modas, usuario_id=carlos, tipo="despesa", valor=750, categoria="Marketing",
            descricao="Anúncios no Instagram", data="2026-10-20",
            texto="gastei 750 com anúncio no instagram", recebida_em="2026-10-20T17:45:00Z",
            ia_valor=750, ia_categoria="Marketing", ia_data="2026-10-20", confianca=0.96,
            status="automatica", criado_em="2026-10-20T17:45:05Z",
            tags=["instagram", "campanha-primavera"],
        ),
    ]

    # Exemplos dos campos opcionais (parcelas e recorrência) no site
    lancamentos += [
        {
            "empresaId": modas,
            "tipo": "despesa",
            "valorCentavos": reais(1200),
            "categoria": "Equipamentos",
            "descricao": "Máquina de cartão (parcela)",
            "data": "2026-10-15",
            "origem": "site",
            "parcelas": {"total": 6, "atual": 2},
            "criadoEm": at("2026-10-15T09:00:00Z"),
        },
        {
            "empresaId": padaria,
            "tipo": "despesa",
            "valorCentavos": reais(89.9),
            "categoria": "Internet",
            "descricao": "Internet da padaria",
            "data": "2026-10-18",
            "origem": "site",
            "recorrencia": {"frequencia": "mensal", "ate": "2027-10-18"},
            "criadoEm": at("2026-10-18T09:00:00Z"),
        },
    ]

    return {"empresas": empresas, "usuarios": usuarios, "lancamentos": lancamentos}
