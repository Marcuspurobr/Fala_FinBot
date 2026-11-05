// Consultas de demonstração em cima dos dados de exemplo. É daqui que sai o painel web.
//   npm run queries
import { pathToFileURL } from "node:url";
import { MongoClient } from "mongodb";
import { requireMongoUri } from "./config.js";

// Traz o nome da empresa para dentro do resultado
const comNomeDaEmpresa = [
  { $lookup: { from: "empresas", localField: "empresaId", foreignField: "_id", as: "empresa" } },
  { $set: { empresa: { $first: "$empresa.nome" } } },
];

export async function runQueries(db) {
  // 1) Receitas, despesas e saldo por empresa e por mês (os indicadores do topo do painel)
  const resumoMensal = await db
    .collection("lancamentos")
    .aggregate([
      {
        $group: {
          _id: { empresaId: "$empresaId", mes: { $substrBytes: ["$data", 0, 7] } },
          receitas: { $sum: { $cond: [{ $eq: ["$tipo", "receita"] }, "$valorCentavos", 0] } },
          despesas: { $sum: { $cond: [{ $eq: ["$tipo", "despesa"] }, "$valorCentavos", 0] } },
        },
      },
      {
        $set: {
          empresaId: "$_id.empresaId",
          mes: "$_id.mes",
          saldo: { $subtract: ["$receitas", "$despesas"] },
        },
      },
      ...comNomeDaEmpresa,
      { $project: { _id: 0, empresaId: 0 } },
      { $sort: { empresa: 1, mes: 1 } },
    ])
    .toArray();

  // 2) Despesas por categoria em cada mês (o gráfico "outubro contra setembro")
  const despesasPorCategoria = await db
    .collection("lancamentos")
    .aggregate([
      { $match: { tipo: "despesa" } },
      {
        $group: {
          _id: { empresaId: "$empresaId", mes: { $substrBytes: ["$data", 0, 7] }, categoria: "$categoria" },
          total: { $sum: "$valorCentavos" },
        },
      },
      { $set: { empresaId: "$_id.empresaId", mes: "$_id.mes", categoria: "$_id.categoria" } },
      ...comNomeDaEmpresa,
      { $project: { _id: 0, empresaId: 0 } },
      { $sort: { empresa: 1, mes: 1, total: -1 } },
    ])
    .toArray();

  // 3) Variação das despesas de outubro em relação a setembro, por empresa e categoria
  const variacaoOutubroSetembro = await db
    .collection("lancamentos")
    .aggregate([
      { $match: { tipo: "despesa", data: { $gte: "2026-09-01", $lt: "2026-11-01" } } },
      {
        $group: {
          _id: { empresaId: "$empresaId", categoria: "$categoria" },
          setembro: { $sum: { $cond: [{ $lt: ["$data", "2026-10-01"] }, "$valorCentavos", 0] } },
          outubro: { $sum: { $cond: [{ $gte: ["$data", "2026-10-01"] }, "$valorCentavos", 0] } },
        },
      },
      {
        $set: {
          empresaId: "$_id.empresaId",
          categoria: "$_id.categoria",
          variacaoPercentual: {
            $cond: [
              { $eq: ["$setembro", 0] },
              null,
              { $round: [{ $multiply: [{ $divide: [{ $subtract: ["$outubro", "$setembro"] }, "$setembro"] }, 100] }, 1] },
            ],
          },
        },
      },
      ...comNomeDaEmpresa,
      { $project: { _id: 0, empresaId: 0 } },
      { $sort: { empresa: 1, categoria: 1 } },
    ])
    .toArray();

  // 4) Lançamentos recentes com a mensagem de origem (o texto que o dono escreveu)
  const recentes = await db
    .collection("lancamentos")
    .aggregate([
      { $sort: { data: -1, criadoEm: -1 } },
      { $limit: 8 },
      { $lookup: { from: "mensagens", localField: "mensagemId", foreignField: "_id", as: "mensagem" } },
      { $set: { mensagemOriginal: { $first: "$mensagem.texto" } } },
      ...comNomeDaEmpresa,
      { $project: { _id: 0, empresa: 1, data: 1, tipo: 1, categoria: 1, valorCentavos: 1, origem: 1, mensagemOriginal: 1 } },
    ])
    .toArray();

  // 5) Taxa de acerto da IA: como cada mensagem terminou
  const acertoDaIA = await db
    .collection("mensagens")
    .aggregate([
      { $group: { _id: { empresaId: "$empresaId", status: "$status" }, mensagens: { $sum: 1 } } },
      { $set: { empresaId: "$_id.empresaId", status: "$_id.status" } },
      ...comNomeDaEmpresa,
      { $project: { _id: 0, empresaId: 0 } },
      { $sort: { empresa: 1, status: 1 } },
    ])
    .toArray();

  // 6) Mensagens que ainda esperam uma resposta do dono
  const pendentes = await db
    .collection("mensagens")
    .aggregate([
      { $match: { status: "pendente" } },
      ...comNomeDaEmpresa,
      {
        $project: {
          _id: 0,
          empresa: 1,
          texto: 1,
          recebidaEm: 1,
          entendeuTipo: "$interpretacao.tipo",
          entendeuValorCentavos: "$interpretacao.valorCentavos",
          confianca: "$interpretacao.confianca",
        },
      },
      { $sort: { recebidaEm: 1 } },
    ])
    .toArray();

  return { resumoMensal, despesasPorCategoria, variacaoOutubroSetembro, recentes, acertoDaIA, pendentes };
}

// Mostra o dinheiro em reais e as datas só com o dia
const brl = (centavos) => (centavos / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const camposEmCentavos = new Set(["receitas", "despesas", "saldo", "total", "setembro", "outubro", "valorCentavos", "entendeuValorCentavos"]);

function printable(rows) {
  return rows.map((row) =>
    Object.fromEntries(
      Object.entries(row).map(([key, value]) => [
        key,
        value instanceof Date
          ? value.toISOString().slice(0, 16).replace("T", " ")
          : camposEmCentavos.has(key) && typeof value === "number"
            ? brl(value)
            : value,
      ])
    )
  );
}

async function main() {
  const client = new MongoClient(requireMongoUri());
  try {
    await client.connect();
    const results = await runQueries(client.db());
    const titles = {
      resumoMensal: "Receitas, despesas e saldo por mês",
      despesasPorCategoria: "Despesas por categoria em cada mês",
      variacaoOutubroSetembro: "Despesas: outubro contra setembro",
      recentes: "Lançamentos recentes (com a mensagem de origem)",
      acertoDaIA: "Como terminaram as mensagens (taxa de acerto da IA)",
      pendentes: "Mensagens aguardando confirmação",
    };
    for (const [key, rows] of Object.entries(results)) {
      console.log(`\n== ${titles[key]} ==`);
      console.table(printable(rows));
    }
  } finally {
    await client.close();
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error("Falhou:", error.message);
    process.exit(1);
  });
}
