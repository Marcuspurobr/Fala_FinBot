// Documentos de exemplo: 2 empresas fictícias, cada uma com 1 usuário, mensagens recebidas pelo chat
// e lançamentos de agosto a novembro de 2026.
// Todos os dados (empresas, e-mails, IDs de chat, valores) são inventados.
import { ObjectId } from "mongodb";

const at = (iso) => new Date(iso);
const reais = (value) => Math.round(value * 100); // R$ 180,00 -> 18000 centavos

// Hash de exemplo (parece um bcrypt, mas não é de nenhuma senha real)
const FAKE_HASH = "$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ0123456";

// Cada linha: [data, tipo, categoria, descrição, valor em reais]
// Fica de fora o que foi lançado pelo chat (vem mais abaixo, ligado à mensagem de origem).
// O mês de novembro vai só até o dia 4.
const PADARIA = [
  ["2026-08-05", "despesa", "Farinha", "Compra de farinha de trigo", 2100],
  ["2026-08-10", "despesa", "Aluguel", "Aluguel do ponto", 3500],
  ["2026-08-12", "despesa", "Energia", "Conta de energia", 1620],
  ["2026-08-31", "receita", "Vendas", "Vendas da semana no balcão", 11800],
  ["2026-09-05", "despesa", "Farinha", "Compra de farinha de trigo", 2250],
  ["2026-09-10", "despesa", "Aluguel", "Aluguel do ponto", 3500],
  ["2026-09-12", "despesa", "Gás", "Botijões de gás", 780],
  ["2026-09-30", "receita", "Vendas", "Vendas do mês no balcão", 13200],
  ["2026-10-10", "despesa", "Aluguel", "Aluguel do ponto", 3500],
  ["2026-10-31", "receita", "Vendas", "Vendas do mês no balcão", 14500],
];

const MODAS = [
  ["2026-08-08", "despesa", "Fornecedores", "Pedido de coleção de verão", 9800],
  ["2026-08-10", "despesa", "Aluguel", "Aluguel da loja", 4200],
  ["2026-08-31", "receita", "Vendas", "Vendas do mês", 21500],
  ["2026-09-08", "despesa", "Fornecedores", "Reposição de estoque", 8700],
  ["2026-09-10", "despesa", "Aluguel", "Aluguel da loja", 4200],
  ["2026-09-18", "despesa", "Marketing", "Anúncios no Instagram", 600],
  ["2026-09-30", "receita", "Vendas", "Vendas do mês", 24300],
  ["2026-10-08", "despesa", "Fornecedores", "Pedido de coleção de primavera", 11200],
  ["2026-10-10", "despesa", "Aluguel", "Aluguel da loja", 4200],
  ["2026-10-31", "receita", "Vendas", "Vendas do mês", 27800],
  ["2026-11-02", "despesa", "Fornecedores", "Compra de vitrines", 3600],
];

export function buildSeedData() {
  // ---------- Empresas ----------
  const padaria = new ObjectId();
  const modas = new ObjectId();

  const empresas = [
    {
      _id: padaria,
      nome: "Padaria Pão Quente",
      segmento: "alimentacao",
      categorias: [
        { nome: "Vendas", tipo: "receita" },
        { nome: "Encomendas", tipo: "receita" },
        { nome: "Farinha", tipo: "despesa" },
        { nome: "Gás", tipo: "despesa" },
        { nome: "Energia", tipo: "despesa" },
        { nome: "Aluguel", tipo: "despesa" },
        { nome: "Internet", tipo: "despesa" },
      ],
      criadaEm: at("2026-08-01T09:00:00Z"),
    },
    {
      _id: modas,
      nome: "Boutique Estação",
      segmento: "varejo",
      categorias: [
        { nome: "Vendas", tipo: "receita" },
        { nome: "Fornecedores", tipo: "despesa" },
        { nome: "Marketing", tipo: "despesa" },
        { nome: "Aluguel", tipo: "despesa" },
        { nome: "Equipamentos", tipo: "despesa" },
      ],
      criadaEm: at("2026-08-03T14:00:00Z"),
    },
  ];

  // ---------- Usuários ----------
  const maria = new ObjectId();
  const carlos = new ObjectId();

  const usuarios = [
    {
      _id: maria,
      empresaId: padaria,
      nome: "Maria Souza",
      email: "maria@paoquente.example",
      senhaHash: FAKE_HASH,
      canalMensagem: { tipo: "telegram", id: "100000001" },
      criadoEm: at("2026-08-01T09:05:00Z"),
    },
    {
      _id: carlos,
      empresaId: modas,
      nome: "Carlos Lima",
      email: "carlos@estacao.example",
      senhaHash: FAKE_HASH,
      canalMensagem: { tipo: "whatsapp", id: "+5534999990001" },
      criadoEm: at("2026-08-03T14:10:00Z"),
    },
  ];

  // ---------- Mensagens (exemplos de cada status) ----------
  // Ids criados antes para os lançamentos poderem apontar para a mensagem de origem
  const msgEnergia = new ObjectId(); // pendente
  const msgGas = new ObjectId(); // confirmada
  const msgFarinha = new ObjectId(); // corrigida (a IA entendeu 2.400, o dono corrigiu para 2.350)
  const msgVendas = new ObjectId(); // automática (confiança alta)
  const msgAnuncio = new ObjectId(); // automática
  const msgVaga = new ObjectId(); // a IA não entendeu: sem interpretação
  const msgErrada = new ObjectId(); // descartada

  const lancGas = new ObjectId();
  const lancFarinha = new ObjectId();
  const lancVendas = new ObjectId();
  const lancAnuncio = new ObjectId();

  const mensagens = [
    {
      _id: msgEnergia,
      empresaId: padaria,
      usuarioId: maria,
      texto: "paguei 180 de energia hoje",
      recebidaEm: at("2026-10-29T22:20:00Z"),
      interpretacao: {
        tipo: "despesa",
        valorCentavos: reais(180),
        categoria: "Energia",
        data: "2026-10-29",
        confianca: 0.94,
      },
      status: "pendente",
    },
    {
      _id: msgGas,
      empresaId: padaria,
      usuarioId: maria,
      texto: "comprei 2 botijões de gás, 820",
      recebidaEm: at("2026-10-12T13:10:00Z"),
      interpretacao: {
        tipo: "despesa",
        valorCentavos: reais(820),
        categoria: "Gás",
        data: "2026-10-12",
        confianca: 0.91,
      },
      status: "confirmada",
      lancamentoId: lancGas,
    },
    {
      _id: msgFarinha,
      empresaId: padaria,
      usuarioId: maria,
      texto: "farinha 2400 ontem",
      recebidaEm: at("2026-10-06T12:00:00Z"),
      interpretacao: {
        tipo: "despesa",
        valorCentavos: reais(2400),
        categoria: "Farinha",
        data: "2026-10-05",
        confianca: 0.82,
      },
      status: "corrigida",
      lancamentoId: lancFarinha,
    },
    {
      _id: msgVendas,
      empresaId: padaria,
      usuarioId: maria,
      texto: "vendi 950 de bolos de encomenda hoje",
      recebidaEm: at("2026-11-03T20:30:00Z"),
      interpretacao: {
        tipo: "receita",
        valorCentavos: reais(950),
        categoria: "Encomendas",
        data: "2026-11-03",
        confianca: 0.97,
      },
      status: "automatica",
      lancamentoId: lancVendas,
    },
    {
      _id: msgAnuncio,
      empresaId: modas,
      usuarioId: carlos,
      texto: "gastei 750 com anúncio no instagram",
      recebidaEm: at("2026-10-20T17:45:00Z"),
      interpretacao: {
        tipo: "despesa",
        valorCentavos: reais(750),
        categoria: "Marketing",
        data: "2026-10-20",
        confianca: 0.96,
      },
      status: "automatica",
      lancamentoId: lancAnuncio,
    },
    {
      _id: msgVaga,
      empresaId: modas,
      usuarioId: carlos,
      texto: "gastei uns trocados no mercado",
      recebidaEm: at("2026-10-22T11:00:00Z"),
      // sem "interpretacao": faltou o valor e a IA perguntou ao dono
      status: "pendente",
    },
    {
      _id: msgErrada,
      empresaId: modas,
      usuarioId: carlos,
      texto: "recebi 5000 do cliente",
      recebidaEm: at("2026-10-25T15:00:00Z"),
      interpretacao: {
        tipo: "receita",
        valorCentavos: reais(5000),
        categoria: "Vendas",
        data: "2026-10-25",
        confianca: 0.7,
      },
      status: "descartada", // o dono disse "não": era um adiantamento, não uma venda
    },
  ];

  // ---------- Lançamentos ----------
  const toLancamento = (empresaId) => ([data, tipo, categoria, descricao, valor]) => ({
    empresaId,
    tipo,
    valorCentavos: reais(valor),
    categoria,
    descricao,
    data,
    origem: "site",
    criadoEm: at(`${data}T12:00:00Z`),
  });

  // Lançamentos feitos pelo site
  const lancamentos = [...PADARIA.map(toLancamento(padaria)), ...MODAS.map(toLancamento(modas))];

  // Lançamentos que vieram do chat (apontam para a mensagem de origem)
  lancamentos.push(
    {
      _id: lancGas,
      empresaId: padaria,
      tipo: "despesa",
      valorCentavos: reais(820),
      categoria: "Gás",
      descricao: "2 botijões de gás",
      data: "2026-10-12",
      origem: "mensagem",
      mensagemId: msgGas,
      criadoEm: at("2026-10-12T13:11:00Z"),
    },
    {
      _id: lancFarinha,
      empresaId: padaria,
      tipo: "despesa",
      valorCentavos: reais(2350), // valor corrigido pelo dono
      categoria: "Farinha",
      descricao: "Compra de farinha de trigo",
      data: "2026-10-05",
      origem: "mensagem",
      mensagemId: msgFarinha,
      criadoEm: at("2026-10-06T12:02:00Z"),
      comprovante: { nomeArquivo: "nota-farinha-out.pdf", url: "https://exemplo.example/comprovantes/nota-farinha-out.pdf" },
    },
    {
      _id: lancVendas,
      empresaId: padaria,
      tipo: "receita",
      valorCentavos: reais(950),
      categoria: "Encomendas",
      descricao: "Bolos de encomenda",
      data: "2026-11-03",
      origem: "mensagem",
      mensagemId: msgVendas,
      criadoEm: at("2026-11-03T20:30:05Z"),
      tags: ["evento"],
    },
    {
      _id: lancAnuncio,
      empresaId: modas,
      tipo: "despesa",
      valorCentavos: reais(750),
      categoria: "Marketing",
      descricao: "Anúncios no Instagram",
      data: "2026-10-20",
      origem: "mensagem",
      mensagemId: msgAnuncio,
      criadoEm: at("2026-10-20T17:45:05Z"),
      tags: ["instagram", "campanha-primavera"],
    }
  );

  // Exemplos dos campos opcionais (parcelas e recorrência) no site
  lancamentos.push(
    {
      empresaId: modas,
      tipo: "despesa",
      valorCentavos: reais(1200),
      categoria: "Equipamentos",
      descricao: "Máquina de cartão (parcela)",
      data: "2026-10-15",
      origem: "site",
      parcelas: { total: 6, atual: 2 },
      criadoEm: at("2026-10-15T09:00:00Z"),
    },
    {
      empresaId: padaria,
      tipo: "despesa",
      valorCentavos: reais(89.9),
      categoria: "Internet",
      descricao: "Internet da padaria",
      data: "2026-10-18",
      origem: "site",
      recorrencia: { frequencia: "mensal", ate: "2027-10-18" },
      criadoEm: at("2026-10-18T09:00:00Z"),
    }
  );

  return { empresas, usuarios, mensagens, lancamentos };
}
