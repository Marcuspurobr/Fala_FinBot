// Cria o banco "lanca", as 4 coleções (com validação e índices) e insere os documentos de exemplo.
//
//   npm run setup        -> cria o que falta; coleções que já têm dados não são mexidas
//   npm run setup:reset  -> apaga as 4 coleções e cria tudo de novo
import { pathToFileURL } from "node:url";
import { MongoClient } from "mongodb";
import { collections } from "./collections.js";
import { buildSeedData } from "./seed-data.js";
import { requireMongoUri } from "./config.js";

export async function setupDatabase(db, { reset = false } = {}) {
  const existing = new Set(
    (await db.listCollections({}, { nameOnly: true }).toArray()).map((c) => c.name)
  );

  if (reset) {
    for (const { name } of collections) {
      if (existing.has(name)) await db.collection(name).drop();
    }
    existing.clear();
  }

  // 1) Coleções + regras de validação + índices
  for (const { name, validator, indexes } of collections) {
    if (!existing.has(name)) {
      await db.createCollection(name, {
        validator,
        validationLevel: "strict", // vale para inserir e para alterar
        validationAction: "error", // documento fora da regra é recusado
      });
    }
    await db.collection(name).createIndexes(indexes);
  }

  // 2) Documentos de exemplo (só em coleções vazias).
  // A ordem importa só para leitura: empresas -> usuários -> mensagens -> lançamentos
  const seed = buildSeedData();
  const summary = [];
  for (const { name } of collections) {
    const collection = db.collection(name);
    if ((await collection.estimatedDocumentCount()) === 0) {
      await collection.insertMany(seed[name]);
    }
    summary.push({ colecao: name, documentos: await collection.countDocuments() });
  }
  return summary;
}

async function main() {
  const reset = process.argv.includes("--reset");
  const client = new MongoClient(requireMongoUri());
  try {
    await client.connect();
    const db = client.db(); // banco definido na connection string
    console.log(`Conectado. Preparando o banco "${db.databaseName}"${reset ? " (reset)" : ""}...`);
    const summary = await setupDatabase(db, { reset });
    console.table(summary);
    console.log("Pronto! Confira no Atlas em Database -> Browse Collections.");
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
