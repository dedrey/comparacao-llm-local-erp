"""Gera banco/dados.sql com dados fictícios para o banco erp_loja.

Só usa a biblioteca padrão. A semente é fixa, então a saída é sempre a mesma.
Uso: python banco/gerar_dados.py
Depois: mysql -u root -p erp_loja < banco/dados.sql
"""

import random
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

SEMENTE = 2026
INICIO = date(2025, 11, 1)
FIM = date(2026, 10, 31)
HOJE = date(2026, 11, 7)  # data de referência para contas vencidas

# Peso de vendas por mês (sazonalidade: pico em dezembro, queda em fevereiro)
PESO_MES = {11: 1.1, 12: 1.9, 1: 0.9, 2: 0.6, 3: 0.8, 4: 0.9,
            5: 1.2, 6: 1.0, 7: 0.9, 8: 0.9, 9: 0.9, 10: 1.0}
VENDAS_BASE = 1420

# Anomalias plantadas
SEMANA_PICO = (date(2026, 7, 13), date(2026, 7, 19))
VENDAS_EXTRAS_PICO = 80
CLIENTE_VIP = 42
VENDAS_CLIENTE_VIP = 25

random.seed(SEMENTE)
saida = []


def dinheiro(valor):
    return Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def sql(valor):
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, (int, Decimal)):
        return str(valor)
    if isinstance(valor, float):
        return f"{valor:.4f}"
    if isinstance(valor, datetime):
        return f"'{valor:%Y-%m-%d %H:%M:%S}'"
    if isinstance(valor, date):
        return f"'{valor:%Y-%m-%d}'"
    return "'" + str(valor).replace("\\", "\\\\").replace("'", "''") + "'"


def inserir(tabela, colunas, linhas, lote=500):
    if not linhas:
        return
    saida.append(f"\n-- {tabela} ({len(linhas)} linhas)")
    for i in range(0, len(linhas), lote):
        valores = ",\n".join("(" + ", ".join(sql(v) for v in linha) + ")"
                             for linha in linhas[i:i + lote])
        saida.append(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES\n{valores};")


def digitos_cpf(base):
    for _ in range(2):
        peso = len(base) + 1
        soma = sum(int(d) * (peso - i) for i, d in enumerate(base))
        resto = (soma * 10) % 11
        base += str(0 if resto == 10 else resto)
    return base


def digitos_cnpj(base):
    for pesos in ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
                  [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]):
        soma = sum(int(d) * p for d, p in zip(base, pesos))
        resto = soma % 11
        base += str(0 if resto < 2 else 11 - resto)
    return base


usados = set()


def novo_doc(tipo):
    while True:
        if tipo == "PF":
            doc = digitos_cpf("".join(random.choices("0123456789", k=9)))
        else:
            doc = digitos_cnpj("".join(random.choices("0123456789", k=8)) + "0001")
        if doc not in usados:
            usados.add(doc)
            return doc


def momento(dia):
    return datetime(dia.year, dia.month, dia.day,
                    random.randint(9, 19), random.randint(0, 59), random.randint(0, 59))


# ------------------------------------------------------------------
# Localização
# ------------------------------------------------------------------
inserir("paises", ["id", "ddi", "sigla", "moeda", "simbolo_moeda", "pais"],
        [(1, "+55", "BRA", "Real", "R$", "Brasil")])

ESTADOS = [(1, "Paraná", "PR"), (2, "Santa Catarina", "SC"),
           (3, "São Paulo", "SP"), (4, "Rio Grande do Sul", "RS")]
inserir("estados", ["id", "pais_id", "estado", "uf"], [(i, 1, n, uf) for i, n, uf in ESTADOS])

CIDADES = [
    ("Foz do Iguaçu", 45, 1, 30), ("Cascavel", 45, 1, 12), ("Curitiba", 41, 1, 10),
    ("Toledo", 45, 1, 6), ("Londrina", 43, 1, 5), ("Medianeira", 45, 1, 6),
    ("Florianópolis", 48, 2, 4), ("Chapecó", 49, 2, 4), ("Joinville", 47, 2, 3),
    ("São Paulo", 11, 3, 5), ("Campinas", 19, 3, 3),
    ("Porto Alegre", 51, 4, 4), ("Caxias do Sul", 54, 4, 2),
]
inserir("cidades", ["id", "cidade", "ddd", "estado_id"],
        [(i, c, ddd, e) for i, (c, ddd, e, _) in enumerate(CIDADES, 1)])
peso_cidade = [p for *_, p in CIDADES]

# ------------------------------------------------------------------
# Cadastros base
# ------------------------------------------------------------------
CATEGORIAS = ["Camisetas", "Camisas", "Calças", "Bermudas", "Vestidos",
              "Saias", "Jaquetas", "Acessórios"]
inserir("categorias", ["id", "categoria"], [(i, c) for i, c in enumerate(CATEGORIAS, 1)])

MARCAS = ["Urbana", "Litoral", "Serra Azul", "Trama", "Nativa", "Basic Co."]
inserir("marcas", ["id", "marca"], [(i, m) for i, m in enumerate(MARCAS, 1)])

inserir("unidades_medida", ["id", "unidade_medida", "descricao"], [(1, "UN", "Unidade")])

CORES = ["Preto", "Branco", "Azul", "Cinza", "Vermelho", "Verde", "Bege", "Rosa"]
inserir("cores", ["id", "nome"], [(i, c) for i, c in enumerate(CORES, 1)])

TAMANHOS = ["PP", "P", "M", "G", "GG", "U"]
inserir("tamanhos", ["id", "nome", "ordem"], [(i, t, i) for i, t in enumerate(TAMANHOS, 1)])

# ------------------------------------------------------------------
# Financeiro base
# ------------------------------------------------------------------
METODOS = [(1, "DIN", "Dinheiro"), (2, "PIX", "PIX"), (3, "CDEB", "Cartão de débito"),
           (4, "CCRE", "Cartão de crédito"), (5, "CRED", "Crediário")]
inserir("metodos_pagamento", ["id", "codigo", "metodo_pagamento"], METODOS)

# id, nome, metodo, parcelas, desconto %, peso de uso
CONDICOES = [
    (1, "Dinheiro à vista", 1, 1, Decimal("5"), 8),
    (2, "PIX à vista", 2, 1, Decimal("5"), 30),
    (3, "Débito à vista", 3, 1, Decimal("0"), 15),
    (4, "Crédito 1x", 4, 1, Decimal("0"), 20),
    (5, "Crédito 3x sem juros", 4, 3, Decimal("0"), 12),
    (6, "Crediário 2x", 5, 2, Decimal("0"), 8),
    (7, "Crediário 3x", 5, 3, Decimal("0"), 7),
    (8, "Boleto 30 dias", 5, 1, Decimal("0"), 0),  # só fornecedores
]
inserir("condicoes_pagamentos",
        ["id", "condicao_pagamento", "metodo_pagamento_id", "numero_parcelas", "desconto_percentual"],
        [(i, n, m, p, d) for i, n, m, p, d, _ in CONDICOES])
inserir("condicoes_pagamentos_parcelas",
        ["condicao_pagamento_id", "numero_parcela", "dias_vencimento"],
        [(i, k, 0 if p == 1 and i < 5 else 30 * k)
         for i, _, _, p, _, _ in CONDICOES for k in range(1, p + 1)])
cond_venda = [c for c in CONDICOES if c[5] > 0]
cond_por_id = {c[0]: c for c in CONDICOES}

# ------------------------------------------------------------------
# Pessoas
# ------------------------------------------------------------------
NOMES_F = ["Ana", "Beatriz", "Camila", "Daniela", "Eduarda", "Fernanda", "Gabriela",
           "Helena", "Isabela", "Juliana", "Larissa", "Mariana", "Natália", "Patrícia",
           "Rafaela", "Sofia", "Tatiane", "Vitória", "Luana", "Carla"]
NOMES_M = ["André", "Bruno", "Carlos", "Diego", "Eduardo", "Felipe", "Gustavo",
           "Henrique", "Igor", "João", "Lucas", "Marcos", "Nicolas", "Otávio",
           "Paulo", "Rafael", "Samuel", "Thiago", "Vinícius", "Leonardo"]
SOBRENOMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves",
              "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho",
              "Rocha", "Almeida", "Nunes", "Mendes", "Barros", "Freitas", "Teixeira",
              "Moreira", "Cardoso", "Vieira", "Schmidt", "Kowalski", "Becker"]
BAIRROS = ["Centro", "Vila A", "Jardim América", "Morumbi", "Porto Meira",
           "Três Lagoas", "Vila Yolanda", "Jardim Central", "Parque Imperatriz"]
RUAS = ["Rua das Flores", "Av. Brasil", "Rua Paraná", "Av. das Cataratas",
        "Rua Almirante Barroso", "Rua Rui Barbosa", "Av. JK", "Rua Tarobá"]


def telefone(ddd):
    return f"({ddd}) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"


clientes = []
for cid in range(1, 151):
    cidade_id = random.choices(range(1, len(CIDADES) + 1), weights=peso_cidade)[0]
    ddd = CIDADES[cidade_id - 1][1]
    if cid % 15 == 0:  # ~7% pessoa jurídica
        nome = f"{random.choice(SOBRENOMES)} {random.choice(['Modas', 'Confecções', 'Uniformes'])} Ltda"
        tipo, sexo = "PJ", "NAO_INFORMAR"
    else:
        feminino = random.random() < 0.6
        primeiro = random.choice(NOMES_F if feminino else NOMES_M)
        nome = f"{primeiro} {random.choice(SOBRENOMES)} {random.choice(SOBRENOMES)}"
        tipo, sexo = "PF", "FEMININO" if feminino else "MASCULINO"
    email = nome.lower().split()[0] + str(cid) + "@email.com"
    for a, b in zip("áéíóúâêôãõç", "aeiouaeoaoc"):
        email = email.replace(a, b)
    criado = momento(INICIO - timedelta(days=random.randint(0, 700)))
    clientes.append((cid, nome, novo_doc(tipo), tipo, sexo, cidade_id,
                     random.choice(RUAS), str(random.randint(10, 3999)), random.choice(BAIRROS),
                     f"85{random.randint(800, 899)}-{random.randint(100, 999)}",
                     telefone(ddd), email, dinheiro(random.choice([0, 500, 1000, 2000])), criado))
inserir("clientes", ["id", "nome_razaosocial", "cpf_cnpj", "tipo_pessoa", "sexo", "cidade_id",
                     "endereco", "numero", "bairro", "cep", "celular", "email",
                     "limite_credito", "criado_em"], clientes)

inserir("emitentes", ["id", "nome_razaosocial", "cnpj", "apelido_nomefantasia", "cidade_id",
                      "endereco", "numero", "bairro", "cep", "telefone", "email", "regime_tributario"],
        [(1, "Loja Modelo Vestuário Ltda", novo_doc("PJ"), "Loja Modelo", 1,
          "Av. Brasil", "1500", "Centro", "85851-000", "(45) 3520-0000",
          "contato@lojamodelo.com", "SIMPLES")])

FORNECEDORES = ["Têxtil Sul", "Malharia Paranaense", "Confecções Catarina", "Jeans Brasil",
                "Moda Paulista", "Fios & Cia", "Acessórios Prime", "Tecelagem Gaúcha"]
CID_FORN = [3, 3, 9, 10, 10, 8, 11, 12]
inserir("fornecedores", ["id", "razaosocial", "cpf_cnpj", "tipo_pessoa", "nomefantasia",
                         "cidade_id", "telefone", "email", "condicao_pagamento_id"],
        [(i, f + " Ltda", novo_doc("PJ"), "PJ", f, CID_FORN[i - 1],
          telefone(CIDADES[CID_FORN[i - 1] - 1][1]),
          f.lower().replace(" ", "").replace("&", "e")[:20] + "@fornecedor.com", 8)
         for i, f in enumerate(FORNECEDORES, 1)])

# ------------------------------------------------------------------
# Produtos e variações
# ------------------------------------------------------------------
# categoria: (modelos, faixa de preço, tamanhos)
MODELOS = {
    1: (["Camiseta Básica", "Camiseta Estampada", "Camiseta Gola V", "Camiseta Oversized", "Regata"], (49, 99), [2, 3, 4, 5]),
    2: (["Camisa Social", "Camisa Linho", "Camisa Xadrez", "Camisa Jeans"], (119, 229), [2, 3, 4, 5]),
    3: (["Calça Jeans Skinny", "Calça Jeans Reta", "Calça Sarja", "Calça Moletom", "Calça Alfaiataria"], (129, 259), [1, 2, 3, 4, 5]),
    4: (["Bermuda Jeans", "Bermuda Sarja", "Bermuda Moletom", "Short Linho"], (79, 149), [2, 3, 4, 5]),
    5: (["Vestido Midi", "Vestido Longo", "Vestido Curto", "Vestido Tubinho", "Vestido Floral"], (139, 299), [1, 2, 3, 4]),
    6: (["Saia Jeans", "Saia Midi", "Saia Plissada", "Saia Curta"], (89, 179), [1, 2, 3, 4]),
    7: (["Jaqueta Jeans", "Jaqueta Couro Sintético", "Jaqueta Corta-Vento", "Moletom Canguru", "Blazer"], (199, 399), [2, 3, 4, 5]),
    8: (["Boné", "Cinto Couro", "Bolsa Transversal", "Meia Kit 3", "Lenço Estampado", "Óculos de Sol", "Carteira", "Mochila"], (29, 159), [6]),
}

produtos, variacoes = [], []
pid = vid = 0
for cat, (modelos, (pmin, pmax), tams) in MODELOS.items():
    for modelo in modelos:
        pid += 1
        marca = random.randint(1, len(MARCAS))
        preco = dinheiro(random.randrange(pmin, pmax + 1, 10) - Decimal("0.10"))
        produtos.append((pid, modelo, f"{modelo} {MARCAS[marca - 1]}", f"789{pid:010d}", cat, marca, 1))
        n_cores = 1 if cat == 8 else random.randint(2, 3)
        for cor in random.sample(range(1, len(CORES) + 1), n_cores):
            for tam in (tams if cat == 8 else random.sample(tams, min(len(tams), random.randint(2, 4)))):
                vid += 1
                variacoes.append({"id": vid, "produto_id": pid, "cor_id": cor, "tam_id": tam,
                                  "preco": preco, "custo": None, "ult_compra": None,
                                  "categoria": cat, "popularidade": random.uniform(0.3, 3.0)})
inserir("produtos", ["id", "produto", "descricao", "codigo_barras", "categoria_id",
                     "marca_id", "unidade_medida_id"], produtos)

# ------------------------------------------------------------------
# Compras (lançadas antes das vendas para definir o custo)
# ------------------------------------------------------------------
estoque = {v["id"]: 0 for v in variacoes}
compras, compras_itens = [], []
datas_compra = [INICIO - timedelta(days=d) for d in (20, 15, 10)]  # carga inicial
datas_compra += sorted(INICIO + timedelta(days=random.randint(0, (FIM - INICIO).days)) for _ in range(57))
fila_inicial = variacoes[:]
random.shuffle(fila_inicial)
lote_inicial = [fila_inicial[i::3] for i in range(3)]

for cpid, emissao in enumerate(datas_compra, 1):
    forn = random.randint(1, len(FORNECEDORES))
    if cpid <= 3:
        itens = lote_inicial[cpid - 1]
    else:  # reposição puxada pelos itens que mais vendem
        itens, n_itens = [], random.randint(15, 30)
        while len(itens) < n_itens:
            v = random.choices(variacoes, weights=[x["popularidade"] for x in variacoes])[0]
            if v not in itens:
                itens.append(v)
    chegada = emissao + timedelta(days=random.randint(2, 7))
    linhas, subtotal = [], Decimal(0)
    for v in itens:
        qtd = int(10 + v["popularidade"] * 10) if cpid <= 3 else random.randint(8, 20)
        custo = (v["preco"] * Decimal(random.uniform(0.42, 0.55))).quantize(Decimal("0.0001"))
        total = dinheiro(custo * qtd)
        subtotal += total
        linhas.append([v, qtd, custo, total])
    frete = dinheiro(subtotal * Decimal("0.03"))
    for v, qtd, custo, total in linhas:
        efetivo = (custo + frete * total / subtotal / qtd).quantize(Decimal("0.0001"))
        compras_itens.append((cpid, v["id"], qtd, custo, total, efetivo))
        estoque[v["id"]] += qtd
        if v["ult_compra"] is None or chegada >= v["ult_compra"]:
            v["custo"], v["ult_compra"] = dinheiro(efetivo), chegada
    chave = "41" + emissao.strftime("%y%m") + "".join(random.choices("0123456789", k=38))
    compras.append((cpid, forn, str(1000 + cpid * 7), "55", 1, chave, emissao, chegada, 8,
                    subtotal, frete, subtotal + frete, "LANCADO", momento(chegada)))

inserir("produto_variacoes", ["id", "produto_id", "cor", "cor_id", "tamanho", "tamanho_id",
                              "codigo_barras", "preco", "preco_custo", "data_ultima_compra"],
        [(v["id"], v["produto_id"], CORES[v["cor_id"] - 1], v["cor_id"], TAMANHOS[v["tam_id"] - 1],
          v["tam_id"], f"79{v['id']:011d}", v["preco"], v["custo"], v["ult_compra"])
         for v in variacoes])
inserir("compras", ["id", "fornecedor_id", "numero_nf", "modelo_nf", "serie_nf", "chave_acesso",
                    "data_emissao", "data_chegada", "condicao_pagamento_id", "valor_subtotal",
                    "valor_frete", "valor_total", "status_compra", "criado_em"], compras)
inserir("compras_itens", ["compra_id", "produto_variacao_id", "quantidade", "valor_unitario",
                          "valor_total", "custo_unitario_efetivo"], compras_itens)

# ------------------------------------------------------------------
# Vendas
# ------------------------------------------------------------------
dias = [INICIO + timedelta(days=d) for d in range((FIM - INICIO).days + 1)]
peso_dia = [PESO_MES[d.month] * (0.4 if d.weekday() == 6 else 1.3 if d.weekday() == 5 else 1.0)
            for d in dias]
datas_venda = random.choices(dias, weights=peso_dia, k=VENDAS_BASE)
datas_venda += [SEMANA_PICO[0] + timedelta(days=random.randint(0, 6)) for _ in range(VENDAS_EXTRAS_PICO)]
datas_venda.sort()

# cliente VIP: sorteia quais vendas são dele
indices_vip = set(random.sample(range(len(datas_venda)), VENDAS_CLIENTE_VIP))
peso_cliente = [random.uniform(0.2, 2.0) for _ in clientes]
peso_cliente[CLIENTE_VIP - 1] = 0  # só recebe as vendas sorteadas acima
peso_var = [v["popularidade"] for v in variacoes]

vendas, vendas_itens, contas, baixas = [], [], [], []
anom_desconto, anom_abaixo_custo = [], []
indices_desconto = set(random.sample(range(len(datas_venda)), 4))
indices_abaixo_custo = set(random.sample(range(len(datas_venda)), 5))

for idx, dia in enumerate(datas_venda):
    vid_ = idx + 1
    vip = idx in indices_vip
    cliente = CLIENTE_VIP if vip else random.choices(range(1, 151), weights=peso_cliente)[0]
    cond = random.choices(cond_venda, weights=[c[5] for c in cond_venda])[0]
    criado = momento(dia)
    if dia >= FIM - timedelta(days=2) and random.random() < 0.5:
        status = "ABERTA"
    elif random.random() < 0.05:
        status = "CANCELADA"
    else:
        status = "FINALIZADA"

    n_itens = random.randint(4, 6) if vip else random.choices([1, 2, 3, 4, 5], weights=[35, 30, 18, 10, 7])[0]
    escolhidas = []
    while len(escolhidas) < n_itens:
        v = random.choices(variacoes, weights=peso_var)[0]
        if v not in escolhidas:
            escolhidas.append(v)
    subtotal = Decimal(0)
    for n, v in enumerate(escolhidas):
        qtd = random.randint(2, 4) if vip else random.choices([1, 2, 3], weights=[75, 20, 5])[0]
        unit = v["preco"]
        if idx in indices_abaixo_custo and n == 0:
            unit = dinheiro(v["custo"] * Decimal("0.75"))
            anom_abaixo_custo.append((vid_, v["id"], unit, v["custo"]))
        total = dinheiro(unit * qtd)
        subtotal += total
        vendas_itens.append((vid_, v["id"], qtd, unit, total, criado))
        if status == "FINALIZADA":
            estoque[v["id"]] -= qtd

    pct = cond[4]
    if idx in indices_desconto:
        pct = Decimal(random.choice([55, 60, 65, 70]))
        anom_desconto.append((vid_, pct))
    elif pct == 0 and random.random() < 0.15:
        pct = Decimal(random.choice([5, 10]))
    desconto = dinheiro(subtotal * pct / 100)
    total_venda = subtotal - desconto
    motivo = "Cliente desistiu da compra" if status == "CANCELADA" else None
    vendas.append((vid_, 1, cliente, cond[0], subtotal, pct, desconto, total_venda,
                   status, motivo, criado, criado))

    # contas a receber do crediário
    if status == "FINALIZADA" and cond[2] == 5:
        parcelas = cond[3]
        base = dinheiro(total_venda / parcelas)
        for k in range(1, parcelas + 1):
            valor = base if k < parcelas else total_venda - base * (parcelas - 1)
            venc = dia + timedelta(days=30 * k)
            cr_id = len(contas) + 1
            if venc <= HOJE - timedelta(days=5) and random.random() < 0.9:
                st, saldo = "RECEBIDA", Decimal(0)
                pago = venc + timedelta(days=random.randint(-3, 10))
                baixas.append((cr_id, min(pago, HOJE), valor, momento(min(pago, HOJE))))
            else:
                st, saldo = "ABERTA", valor
            contas.append((cr_id, cliente, vid_, f"Venda {vid_} - parcela {k}/{parcelas}",
                           venc, valor, saldo, st, criado))

inserir("vendas", ["id", "emitente_id", "cliente_id", "condicao_pagamento_id", "valor_subtotal",
                   "desconto_percentual_aplicado", "valor_desconto", "valor_total", "status_venda",
                   "motivo_cancelamento", "criado_em", "atualizado_em"], vendas)
inserir("vendas_itens", ["venda_id", "produto_variacao_id", "quantidade", "valor_unitario",
                         "valor_total", "criado_em"], vendas_itens)
inserir("contas_receber", ["id", "cliente_id", "venda_id", "descricao", "data_vencimento",
                           "valor_original", "valor_saldo", "status", "criado_em"], contas)
inserir("contas_receber_baixas", ["conta_receber_id", "data_recebimento", "valor_recebido",
                                  "criado_em"], baixas)

# ------------------------------------------------------------------
# Estoque (compras - vendas finalizadas) com anomalias plantadas
# ------------------------------------------------------------------
baixo = [v for v, q in estoque.items() if q <= 0]
assert not baixo, f"estoque natural <= 0 nas variações {baixo}; ajuste as compras"
candidatas = random.sample(sorted(estoque), 5)
anom_estoque = {candidatas[0]: 0, candidatas[1]: 0, candidatas[2]: 0,
                candidatas[3]: -2, candidatas[4]: -5}
estoque.update(anom_estoque)
inserir("estoque", ["produto_variacao_id", "quantidade", "atualizado_em"],
        [(v, q, datetime(2026, 10, 31, 20, 0, 0)) for v, q in sorted(estoque.items())])

# ------------------------------------------------------------------
# Arquivo final
# ------------------------------------------------------------------
cabecalho = [
    "-- Dados fictícios do erp_loja. Gerado por banco/gerar_dados.py (semente %d). Não editar à mão." % SEMENTE,
    "-- Anomalias plantadas:",
    "--   semana de pico: %s a %s (+%d vendas)" % (SEMANA_PICO[0], SEMANA_PICO[1], VENDAS_EXTRAS_PICO),
    "--   cliente com compras muito acima da média: id %d (%d vendas grandes)" % (CLIENTE_VIP, VENDAS_CLIENTE_VIP),
    "--   vendas com desconto acima de 50%%: %s" % ", ".join(f"{v} ({p}%)" for v, p in anom_desconto),
    "--   itens vendidos abaixo do custo (venda, variação): %s" % ", ".join(f"({v}, {pv})" for v, pv, *_ in anom_abaixo_custo),
    "--   estoque zerado ou negativo (variação: qtd): %s" % ", ".join(f"{v}: {q}" for v, q in anom_estoque.items()),
    "",
    "USE erp_loja;",
    "SET NAMES utf8mb4;",
]
saida.append("")
destino = Path(__file__).with_name("dados.sql")
destino.write_text("\n".join(cabecalho + saida), encoding="utf-8")

print(f"Gerado {destino}")
print(f"produtos={len(produtos)} variacoes={len(variacoes)} clientes={len(clientes)} "
      f"compras={len(compras)} vendas={len(vendas)} itens={len(vendas_itens)} "
      f"contas_receber={len(contas)} baixas={len(baixas)}")
print("\n".join(cabecalho[1:7]))
