# Lança: modelo de dados em MongoDB

Repositório acadêmico da disciplina de NoSQL. Ele reúne a descrição do sistema **Lança** (nome provisório) e o código que cria o banco, as coleções e documentos de exemplo no MongoDB online (MongoDB Atlas).

## 1. Descrição do sistema

O Lança é um sistema de administração financeira para pequenos negócios. O dono da padaria, da loja de roupas ou da clínica lança receitas e despesas de duas formas: pelo site, preenchendo um formulário, ou simplesmente mandando uma mensagem em um chat, como "paguei 180 de energia hoje". Uma inteligência artificial lê o texto, descobre se é receita ou despesa, o valor, a categoria e a data, e registra o lançamento. Um painel web compara receitas e despesas entre meses e categorias.

### O problema

Todo dono de negócio precisa saber quanto entra e quanto sai, mas a maioria desiste de controlar porque registrar tudo em planilhas ou em sistemas cheios de campos dá trabalho. Sem controle, ele descobre que o mês fechou no vermelho só quando o dinheiro já acabou.

### Como o sistema resolve

A entrada de dados fica tão simples quanto mandar uma mensagem. O fluxo de uma mensagem é este:

1. O dono escreve no chat, em texto livre.
2. O sistema identifica quem é o usuário e de qual empresa ele é, e manda a mensagem para a IA junto com a data de hoje e as categorias daquela empresa.
3. A IA devolve uma interpretação (tipo, valor, categoria, data e um grau de confiança), que fica guardada na própria mensagem.
4. Se a confiança for baixa ou faltar alguma informação, o sistema pergunta ao dono antes de gravar. Se for alta, pode gravar direto e avisar, com a opção de desfazer.
5. Confirmada a interpretação, o sistema cria o lançamento, que é o registro oficial e alimenta o painel.

A IA só interpreta o texto. As somas, os comparativos e os filtros do painel são feitos pelo banco, que é exato.

### Várias empresas no mesmo sistema

Muitos negócios usam o mesmo sistema, mas um nunca enxerga os dados do outro. Por isso quase todo documento carrega o `empresaId`, e as consultas sempre filtram por ele. Cada empresa também define as próprias categorias: uma padaria tem "Farinha" e "Gás", uma loja de roupas tem "Fornecedores" e "Marketing".

### O que o sistema não faz

Ele controla o fluxo de caixa. Não gera balanço patrimonial, e uma DRE completa também ficaria de fora, porque o registro é feito pelo regime de caixa, quando o dinheiro entra ou sai.

### Por que MongoDB

Os pontos em que o modelo de documento ajuda de verdade são três. O primeiro é a interpretação da IA, que tem formato variável e fica guardada junto com o texto original e o status, o que dá um histórico do que a IA entendeu e permite medir a taxa de acerto. O segundo são os campos opcionais dos lançamentos: um lançamento simples tem só os campos básicos, e um parcelado, recorrente ou com comprovante carrega a mais o que precisa, sem colunas vazias. O terceiro é que as categorias de cada empresa ficam dentro do documento dela, sem tabela extra.

Para ser honesto, esse sistema também poderia ser feito em um banco relacional, e um Postgres com campos JSON resolveria boa parte. A escolha pelo MongoDB aqui se apoia no encaixe do modelo de documento com o fluxo de mensagens e interpretações, e não em uma limitação do SQL. Mesmo sendo flexível, o banco valida os documentos com `$jsonSchema`, para não aceitar dado errado, e o dinheiro é guardado em centavos, como número inteiro, para não ter erro de arredondamento.

## 2. O banco de dados

O banco se chama `lanca` e tem 4 coleções:

| Coleção | O que guarda |
|---|---|
| `empresas` | Cada negócio que usa o sistema, com o segmento e as categorias de receita e despesa que ele definiu |
| `usuarios` | O dono (ou quem a empresa autoriza): login por e-mail e senha (só o hash) e o canal do chat, que liga a mensagem à empresa certa |
| `mensagens` | Tudo que chega pelo chat, antes de virar lançamento: texto original, interpretação da IA e status |
| `lancamentos` | O registro oficial de receitas e despesas, vindo do chat ou do site. É a base do painel |

As ligações entre elas são feitas por identificadores. `usuarios`, `mensagens` e `lancamentos` apontam para a empresa por `empresaId`. A mensagem aponta para o lançamento que gerou (`lancamentoId`) e o lançamento aponta de volta para a mensagem de origem (`mensagemId`), o que dá a trilha de auditoria. Lançamentos feitos pelo site não passam por `mensagens` e não têm `mensagemId`.

O status de uma mensagem pode ser `pendente` (esperando o dono), `confirmada`, `corrigida` (o dono ajustou algum campo), `automatica` (gravada sem perguntar, por confiança alta) ou `descartada` (o dono recusou).

Um exemplo de documento da coleção `mensagens`:

```json
{
  "empresaId": "ObjectId(...)",
  "usuarioId": "ObjectId(...)",
  "texto": "paguei 180 de energia hoje",
  "recebidaEm": "2026-10-29T22:20:00Z",
  "interpretacao": {
    "tipo": "despesa",
    "valorCentavos": 18000,
    "categoria": "Energia",
    "data": "2026-10-29",
    "confianca": 0.94
  },
  "status": "pendente"
}
```

## 3. Estrutura do repositório

```
lanca-mongodb/
├── README.md             este arquivo
├── .env.example          modelo do arquivo .env (a connection string)
├── package.json
└── src/
    ├── config.js         lê a connection string do arquivo .env
    ├── collections.js    as 4 coleções: regras de validação ($jsonSchema) e índices
    ├── seed-data.js      documentos de exemplo (2 empresas fictícias)
    └── setup.js          cria o banco, as coleções, os índices e insere os exemplos
```

## 4. Como rodar

Você precisa do [Node.js](https://nodejs.org) 22.9 ou mais novo e de uma conta gratuita no [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register).

### Criar o banco online

1. No Atlas, clique em **Create**, escolha o cluster gratuito **M0 (Free)**, a região **São Paulo (sa-east-1)** e crie o cluster.
2. Crie o usuário do banco (usuário e senha) e guarde a senha.
3. Em **Network Access**, adicione o seu IP com **Add Current IP Address**.
4. Em **Database, Connect, Drivers**, copie a connection string (`mongodb+srv://...`) e troque `<db_password>` pela senha do passo 2.

### Configurar e executar

```bash
git clone <endereço deste repositório>
cd lanca-mongodb
npm install
cp .env.example .env      # depois edite o .env e cole a sua connection string, terminando em /lanca
npm run setup             # cria o banco "lanca", as 4 coleções, os índices e os exemplos
```

O arquivo `.env` não vai para o repositório (está no `.gitignore`), então a senha do banco fica só na sua máquina.

| Comando | O que faz |
|---|---|
| `npm run setup` | Cria o que falta. Coleções que já têm dados não são alteradas |
| `npm run setup:reset` | Apaga as 4 coleções e cria tudo de novo |

Depois do `npm run setup`, os dados aparecem no Atlas em **Database, Browse Collections, lanca**.

Todos os dados de exemplo (empresas, e-mails, identificadores de chat, valores) são fictícios. O hash de senha dos usuários de exemplo também é inventado e não corresponde a nenhuma senha real.


## 5. Consultas (views)

As duas consultas abaixo foram criadas no MongoDB Atlas como views da coleção `lancamentos`. Cada uma é um aggregation pipeline, ou seja, uma sequência de estágios em que a saída de um alimenta o próximo. Os valores estão guardados em centavos.

### View `Funcionalidade1`: despesas por categoria

Mostra quanto foi gasto em cada categoria, da maior despesa para a menor. Serve para o dono ver rapidamente onde o dinheiro está indo.

1. `$match` deixa passar só os lançamentos do tipo despesa.
2. `$group` agrupa os lançamentos pela categoria e soma o valor de cada grupo.
3. `$sort` ordena do maior total para o menor.

```js
[
  { $match: { tipo: "despesa" } },
  { $group: { _id: "$categoria", total: { $sum: "$valorCentavos" } } },
  { $sort: { total: -1 } }
]
```

Com os dados de exemplo, a categoria com maior gasto é Fornecedores, e a menor é Internet. Como a coleção reúne as duas empresas de exemplo, categorias com o mesmo nome (como Aluguel) aparecem somadas.

![Resultado da view Funcionalidade1](prints/funcionalidade1.png)

### View `Funcionalidade2`: resumo mensal

Compara receitas e despesas de cada mês e calcula o saldo (receitas menos despesas). Serve para acompanhar se o negócio fechou o mês no azul ou no vermelho.

1. `$group` agrupa os lançamentos por mês, recortando os sete primeiros caracteres da data (por exemplo, `2026-10`). Em cada grupo, um `$cond` soma o valor só dos lançamentos de receita em um campo e só dos de despesa em outro.
2. `$project` mostra o mês, as receitas e as despesas, e cria o campo `saldo` com a diferença entre os dois.
3. `$sort` ordena os meses do mais antigo para o mais recente.

```js
[
  { $group: {
      _id: { $substrBytes: ["$data", 0, 7] },
      receitas: { $sum: { $cond: [ { $eq: ["$tipo", "receita"] }, "$valorCentavos", 0 ] } },
      despesas: { $sum: { $cond: [ { $eq: ["$tipo", "despesa"] }, "$valorCentavos", 0 ] } }
  } },
  { $project: { _id: 0, mes: "$_id", receitas: 1, despesas: 1, saldo: { $subtract: ["$receitas", "$despesas"] } } },
  { $sort: { mes: 1 } }
]
```

Com os dados de exemplo, os meses de agosto a outubro fecham com saldo positivo. Novembro aparece negativo porque os lançamentos de exemplo só vão até o início do mês e as despesas dos primeiros dias vieram antes das vendas.

![Resultado da view Funcionalidade2](prints/funcionalidade2.png)