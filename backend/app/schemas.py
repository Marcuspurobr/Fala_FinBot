"""Definição das 3 coleções do banco "finbot".

Cada coleção tem:
  - validator: regras ($jsonSchema) que o MongoDB confere antes de aceitar um documento;
  - indexes: índices para buscas rápidas e para garantir valores únicos.
"""
from pymongo import ASCENDING, DESCENDING, IndexModel

# ---------- Pequenos atalhos para escrever os schemas ----------
object_id = {"bsonType": "objectId"}
string = {"bsonType": "string", "minLength": 1}
date = {"bsonType": "date"}
cents = {"bsonType": ["int", "long"], "minimum": 1}  # dinheiro em centavos (inteiro, sem erro de arredondamento)


def one_of(*values):
    return {"bsonType": "string", "enum": list(values)}


def pattern(regex):
    return {"bsonType": "string", "pattern": regex}


EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
DAY = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"  # data do lançamento no formato AAAA-MM-DD


def subdocument(required, properties):
    """Subdocumento (fica dentro de outro documento, sem _id próprio)."""
    return {
        "bsonType": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


def document(required, properties):
    """Documento principal da coleção (inclui o _id)."""
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": required,
            "properties": {"_id": object_id, **properties},
            "additionalProperties": False,
        }
    }


# ---------- As coleções ----------
COLLECTIONS = [
    {
        # Empresas: cada negócio que usa o sistema, com as categorias que ele mesmo definiu
        "name": "empresas",
        "validator": document(
            ["nome", "segmento", "categorias", "criadaEm"],
            {
                "nome": string,
                "segmento": one_of("varejo", "alimentacao", "servicos", "saude", "outro"),
                "categorias": {
                    "bsonType": "array",
                    "minItems": 1,
                    "items": subdocument(
                        ["nome", "tipo"],
                        {"nome": string, "tipo": one_of("receita", "despesa")},
                    ),
                },
                "criadaEm": date,
            },
        ),
        "indexes": [IndexModel([("nome", ASCENDING)], name="nome_empresa")],
    },
    {
        # Usuários: o dono (ou quem a empresa autoriza). Faz o login no site e liga o chat à empresa
        "name": "usuarios",
        "validator": document(
            ["empresaId", "nome", "email", "senhaHash", "criadoEm"],
            {
                "empresaId": object_id,
                "nome": string,
                "email": pattern(EMAIL),
                "senhaHash": string,  # nunca a senha em texto: só o hash (bcrypt ou argon2)
                # Canal de mensagem (opcional): de qual chat o usuário manda os lançamentos
                "canalMensagem": subdocument(
                    ["tipo", "id"],
                    {"tipo": one_of("telegram", "whatsapp"), "id": string},
                ),
                "criadoEm": date,
            },
        ),
        "indexes": [
            IndexModel([("email", ASCENDING)], name="email_unico", unique=True),
            IndexModel([("empresaId", ASCENDING)], name="usuarios_da_empresa"),
            IndexModel(
                # Um chat pertence a um único usuário (só vale para quem tem canal cadastrado)
                [("canalMensagem.tipo", ASCENDING), ("canalMensagem.id", ASCENDING)],
                name="canal_unico",
                unique=True,
                partialFilterExpression={"canalMensagem.id": {"$exists": True}},
            ),
        ],
    },
    {
        # Lançamentos: o registro oficial de receitas e despesas. É daqui que sai o painel.
        # Quando o lançamento veio do chat, a mensagem original (texto, interpretação da IA e status)
        # fica embutida no campo "mensagem". Não existe coleção separada para mensagens.
        # Os campos opcionais (mensagem, parcelas, recorrencia, comprovante, tags) variam de documento para documento.
        "name": "lancamentos",
        "validator": {
            **document(
                ["empresaId", "tipo", "valorCentavos", "categoria", "descricao", "data", "origem", "criadoEm"],
                {
                    "empresaId": object_id,
                    "tipo": one_of("receita", "despesa"),
                    "valorCentavos": cents,
                    "categoria": string,
                    "descricao": string,
                    "data": pattern(DAY),
                    "origem": one_of("mensagem", "site"),
                    # Mensagem de chat que gerou o lançamento (só quando origem = "mensagem")
                    "mensagem": subdocument(
                        ["usuarioId", "texto", "recebidaEm", "status"],
                        {
                            "usuarioId": object_id,
                            "texto": string,
                            "recebidaEm": date,
                            # Resposta da IA. Ausente quando a IA não conseguiu entender a mensagem
                            "interpretacao": subdocument(
                                ["tipo", "valorCentavos", "categoria", "data", "confianca"],
                                {
                                    "tipo": one_of("receita", "despesa"),
                                    "valorCentavos": cents,
                                    "categoria": string,
                                    "data": pattern(DAY),
                                    "confianca": {"bsonType": "number", "minimum": 0, "maximum": 1},
                                },
                            ),
                            # confirmada: o dono disse "sim" | corrigida: o dono ajustou algum campo
                            # automatica: gravada sem perguntar (confiança alta)
                            "status": one_of("confirmada", "corrigida", "automatica"),
                        },
                    ),
                    # ---- campos opcionais ----
                    "parcelas": subdocument(
                        ["total", "atual"],
                        {
                            "total": {"bsonType": "int", "minimum": 2},
                            "atual": {"bsonType": "int", "minimum": 1},
                        },
                    ),
                    "recorrencia": subdocument(
                        ["frequencia"],
                        {
                            "frequencia": one_of("semanal", "mensal", "anual"),
                            "ate": pattern(DAY),
                        },
                    ),
                    "comprovante": subdocument(
                        ["nomeArquivo", "url"],
                        {"nomeArquivo": string, "url": string},
                    ),
                    "tags": {"bsonType": "array", "uniqueItems": True, "items": string},
                    "criadoEm": date,
                },
            ),
            # Veio do chat => tem mensagem. Veio do site => não tem
            "$or": [
                {"origem": "mensagem", "mensagem": {"$exists": True}},
                {"origem": "site", "mensagem": {"$exists": False}},
            ],
        },
        "indexes": [
            IndexModel([("empresaId", ASCENDING), ("data", DESCENDING)], name="empresa_data"),
            IndexModel(
                [("empresaId", ASCENDING), ("tipo", ASCENDING), ("categoria", ASCENDING), ("data", ASCENDING)],
                name="empresa_tipo_categoria_data",
            ),
            # Só para lançamentos vindos do chat: mensagens de um usuário e status das mensagens por empresa
            IndexModel(
                [("mensagem.usuarioId", ASCENDING), ("mensagem.recebidaEm", DESCENDING)],
                name="mensagens_do_usuario",
                sparse=True,
            ),
            IndexModel(
                [("empresaId", ASCENDING), ("mensagem.status", ASCENDING)],
                name="empresa_status_mensagem",
                sparse=True,
            ),
        ],
    },
]
