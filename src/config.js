// Lê a connection string do MongoDB do arquivo .env (carregado pelo Node com --env-file-if-exists).
// O nome do banco vem dentro da própria connection string (ex.: ...mongodb.net/kivo).
import dns from "node:dns";

// Em algumas redes (empresa/VPN) o DNS local recusa a consulta SRV que o endereço
// "mongodb+srv://" do Atlas precisa. Usar DNS públicos primeiro evita esse erro.
dns.setServers(["8.8.8.8", "1.1.1.1", ...dns.getServers()]);

export function requireMongoUri() {
  const uri = process.env.MONGODB_URI;
  if (!uri) {
    console.error("MONGODB_URI não configurada no arquivo .env.");
    process.exit(1);
  }
  return uri;
}
