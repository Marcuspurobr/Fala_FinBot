// Definição das 4 coleções do banco "finbot".
// Cada coleção tem:
//   - validator: regras ($jsonSchema) que o MongoDB confere antes de aceitar um documento;
//   - indexes: índices para buscas rápidas e para garantir valores únicos.

// ---------- Pequenos atalhos para escrever os schemas ----------
const objectId = { bsonType: "objectId" };
const string = { bsonType: "string", minLength: 1 };
const date = { bsonType: "date" };
const cents = { bsonType: ["int", "long"], minimum: 1 }; // dinheiro em centavos (inteiro, sem erro de arredondamento)
const oneOf = (...values) => ({ bsonType: "string", enum: values });
const pattern = (regex) => ({ bsonType: "string", pattern: regex });

const EMAIL = "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$";
const DAY = "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"; // data do lançamento no formato AAAA-MM-DD

// Subdocumento (fica dentro de outro documento, sem _id próprio)
function subdocument(required, properties) {
  return { bsonType: "object", required, properties, additionalProperties: false };
}

// Documento principal da coleção (inclui o _id)
function document(required, properties) {
  return {
    $jsonSchema: {
      bsonType: "object",
      required,
      properties: { _id: objectId, ...properties },
      additionalProperties: false,
    },
  };
}

// ---------- As coleções ----------
export const collections = [
  {
    // Empresas: cada negócio que usa o sistema, com as categorias que ele mesmo definiu
    name: "empresas",
    validator: document(["nome", "segmento", "categorias", "criadaEm"], {
      nome: string,
      segmento: oneOf("varejo", "alimentacao", "servicos", "saude", "outro"),
      categorias: {
        bsonType: "array",
        minItems: 1,
        items: subdocument(["nome", "tipo"], {
          nome: string,
          tipo: oneOf("receita", "despesa"),
        }),
      },
      criadaEm: date,
    }),
    indexes: [{ key: { nome: 1 }, name: "nome_empresa" }],
  },

  {
    // Usuários: o dono (ou quem a empresa autoriza). Faz o login no site e liga o chat à empresa
    name: "usuarios",
    validator: document(["empresaId", "nome", "email", "senhaHash", "criadoEm"], {
      empresaId: objectId,
      nome: string,
      email: pattern(EMAIL),
      senhaHash: string, // nunca a senha em texto: só o hash (bcrypt ou argon2)
      // Canal de mensagem (opcional): de qual chat o usuário manda os lançamentos
      canalMensagem: subdocument(["tipo", "id"], {
        tipo: oneOf("telegram", "whatsapp"),
        id: string,
      }),
      criadoEm: date,
    }),
    indexes: [
      { key: { email: 1 }, name: "email_unico", unique: true },
      { key: { empresaId: 1 }, name: "usuarios_da_empresa" },
      {
        // Um chat pertence a um único usuário (só vale para quem tem canal cadastrado)
        key: { "canalMensagem.tipo": 1, "canalMensagem.id": 1 },
        name: "canal_unico",
        unique: true,
        partialFilterExpression: { "canalMensagem.id": { $exists: true } },
      },
    ],
  },

  {
    // Mensagens: tudo que chega pelo chat, ANTES de virar lançamento.
    // Guarda o texto original e o que a IA entendeu (a "interpretacao").
    name: "mensagens",
    validator: document(["empresaId", "usuarioId", "texto", "recebidaEm", "status"], {
      empresaId: objectId,
      usuarioId: objectId,
      texto: string,
      recebidaEm: date,
      // Resposta da IA. Ausente quando a IA não conseguiu entender a mensagem
      interpretacao: subdocument(["tipo", "valorCentavos", "categoria", "data", "confianca"], {
        tipo: oneOf("receita", "despesa"),
        valorCentavos: cents,
        categoria: string,
        data: pattern(DAY),
        confianca: { bsonType: "number", minimum: 0, maximum: 1 },
      }),
      // pendente: aguardando o dono | confirmada: o dono disse "sim" | corrigida: o dono ajustou
      // automatica: gravada sem perguntar (confiança alta) | descartada: o dono recusou
      status: oneOf("pendente", "confirmada", "corrigida", "automatica", "descartada"),
      lancamentoId: objectId, // preenchido quando a mensagem virou lançamento
    }),
    indexes: [
      { key: { empresaId: 1, status: 1, recebidaEm: -1 }, name: "empresa_status_data" },
      { key: { usuarioId: 1, recebidaEm: -1 }, name: "mensagens_do_usuario" },
    ],
  },

  {
    // Lançamentos: o registro oficial de receitas e despesas. É daqui que sai o painel.
    // Os campos opcionais (parcelas, recorrencia, comprovante, tags) variam de documento para documento.
    name: "lancamentos",
    validator: {
      ...document(
        ["empresaId", "tipo", "valorCentavos", "categoria", "descricao", "data", "origem", "criadoEm"],
        {
          empresaId: objectId,
          tipo: oneOf("receita", "despesa"),
          valorCentavos: cents,
          categoria: string,
          descricao: string,
          data: pattern(DAY),
          origem: oneOf("mensagem", "site"),
          mensagemId: objectId, // só quando origem = "mensagem"
          // ---- campos opcionais ----
          parcelas: subdocument(["total", "atual"], {
            total: { bsonType: "int", minimum: 2 },
            atual: { bsonType: "int", minimum: 1 },
          }),
          recorrencia: subdocument(["frequencia"], {
            frequencia: oneOf("semanal", "mensal", "anual"),
            ate: pattern(DAY),
          }),
          comprovante: subdocument(["nomeArquivo", "url"], {
            nomeArquivo: string,
            url: string,
          }),
          tags: { bsonType: "array", uniqueItems: true, items: string },
          criadoEm: date,
        }
      ),
      // Veio do chat => tem mensagemId. Veio do site => não tem
      $or: [
        { origem: "mensagem", mensagemId: { $exists: true } },
        { origem: "site", mensagemId: { $exists: false } },
      ],
    },
    indexes: [
      { key: { empresaId: 1, data: -1 }, name: "empresa_data" },
      { key: { empresaId: 1, tipo: 1, categoria: 1, data: 1 }, name: "empresa_tipo_categoria_data" },
      { key: { mensagemId: 1 }, name: "mensagem_de_origem", sparse: true },
    ],
  },
];
