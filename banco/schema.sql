-- Schema do ERP acadêmico de loja de roupas.
-- Origem: github.com/dedrey/SI_Andrey_Teodoro_2026 (Data/banco.txt), já com a migração de casas decimais.
-- Única mudança: nome do banco (erp_loja) e DROP/CREATE para poder recriar do zero.

DROP DATABASE IF EXISTS erp_loja;
CREATE DATABASE erp_loja CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE erp_loja;

-- ================================================================
-- 0. PERFIS (perfis de acesso dos usuários — Vendedor, Gerente, etc.)
-- ================================================================
CREATE TABLE perfis (
  id        INT         AUTO_INCREMENT PRIMARY KEY,
  nome      VARCHAR(30) NOT NULL UNIQUE,
  ativo     TINYINT(1)  NOT NULL DEFAULT 1,
  criado_em DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO perfis (nome) VALUES ('Vendedor'), ('Gerente'), ('Proprietário(a)'), ('Admin');

-- ================================================================
-- 1. USUÁRIOS
-- ================================================================
CREATE TABLE usuarios (
  id             INT          AUTO_INCREMENT PRIMARY KEY,
  nome           VARCHAR(75)  NOT NULL,
  usuario        VARCHAR(50)  NOT NULL UNIQUE,
  email          VARCHAR(50)  NOT NULL UNIQUE,
  cpf            VARCHAR(11)  NOT NULL UNIQUE,
  telefone       VARCHAR(15),
  perfil_id      INT NULL,
  senha_hash     VARCHAR(255) NOT NULL,
  ativo          BOOLEAN      NOT NULL DEFAULT TRUE,
  criado_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  criado_por     INT NULL,
  atualizado_por INT NULL,
  CONSTRAINT fk_usuarios_perfil         FOREIGN KEY (perfil_id)      REFERENCES perfis(id)   ON DELETE SET NULL,
  CONSTRAINT fk_usuarios_criado_por     FOREIGN KEY (criado_por)     REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_usuarios_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 2. LOCALIZAÇÃO
-- ================================================================
CREATE TABLE paises (
  id             INT         AUTO_INCREMENT PRIMARY KEY,
  ddi            VARCHAR(5)  NOT NULL,
  sigla          CHAR(3)     NOT NULL UNIQUE,
  moeda          VARCHAR(30) NOT NULL,
  simbolo_moeda  VARCHAR(5)  NOT NULL,
  pais           VARCHAR(50) NOT NULL UNIQUE,
  ativo          BOOLEAN     NOT NULL DEFAULT TRUE,
  criado_em      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  criado_por     INT NULL,
  atualizado_por INT NULL,
  CONSTRAINT fk_paises_criado_por     FOREIGN KEY (criado_por)     REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_paises_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE estados (
  id             INT         AUTO_INCREMENT PRIMARY KEY,
  pais_id        INT         NOT NULL,
  estado         VARCHAR(50) NOT NULL,
  uf             CHAR(2)     NOT NULL,
  ativo          BOOLEAN     NOT NULL DEFAULT TRUE,
  criado_em      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  criado_por     INT NULL,
  atualizado_por INT NULL,
  CONSTRAINT fk_estados_pais            FOREIGN KEY (pais_id)        REFERENCES paises(id)   ON DELETE NO ACTION,
  CONSTRAINT fk_estados_criado_por      FOREIGN KEY (criado_por)     REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_estados_atualizado_por  FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT unique_uf_pais             UNIQUE (pais_id, uf)
) ENGINE=InnoDB;

CREATE TABLE cidades (
  id             INT         AUTO_INCREMENT PRIMARY KEY,
  cidade         VARCHAR(50) NOT NULL,
  ddd            SMALLINT    NOT NULL,
  estado_id      INT         NOT NULL,
  ativo          BOOLEAN     NOT NULL DEFAULT TRUE,
  criado_em      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  criado_por     INT NULL,
  atualizado_por INT NULL,
  CONSTRAINT fk_cidades_estado          FOREIGN KEY (estado_id)      REFERENCES estados(id)  ON DELETE NO ACTION,
  CONSTRAINT fk_cidades_criado_por      FOREIGN KEY (criado_por)     REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_cidades_atualizado_por  FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT unique_cidade_estado       UNIQUE (cidade, estado_id)
) ENGINE=InnoDB;

-- ================================================================
-- 3. FORNECEDORES
-- ================================================================
CREATE TABLE fornecedores (
  id             INT          AUTO_INCREMENT PRIMARY KEY,
  razaosocial    VARCHAR(100) NOT NULL UNIQUE,
  cpf_cnpj       VARCHAR(14)  NOT NULL UNIQUE,
  tipo_pessoa    VARCHAR(2) NOT NULL DEFAULT 'PJ',
  nomefantasia   VARCHAR(100),
  cidade_id      INT NULL,
  endereco       VARCHAR(50),
  numero         VARCHAR(10),
  complemento    VARCHAR(50),
  bairro         VARCHAR(50),
  cep            VARCHAR(9)   NULL COMMENT 'CEP no formato 00000-000',
  telefone       VARCHAR(15),
  email          VARCHAR(50),
  condicao_pagamento_id INT NULL,
  ativo          BOOLEAN      NOT NULL DEFAULT TRUE,
  criado_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por     INT NULL,
  atualizado_em  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por INT NULL,
  CONSTRAINT fk_fornecedores_cidade
    FOREIGN KEY (cidade_id) REFERENCES cidades(id) ON DELETE SET NULL,
  CONSTRAINT fk_fornecedores_criado_por
    FOREIGN KEY (criado_por) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_fornecedores_atualizado_por
    FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 4. CADASTROS BASE
-- ================================================================
CREATE TABLE categorias (
  id             INT         AUTO_INCREMENT PRIMARY KEY,
  categoria      VARCHAR(50) NOT NULL UNIQUE,
  ativo          BOOLEAN     NOT NULL DEFAULT TRUE,
  criado_em      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por     INT NULL,
  atualizado_em  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por INT NULL,
  CONSTRAINT fk_categorias_criado_por     FOREIGN KEY (criado_por)     REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_categorias_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE marcas (
  id             INT         AUTO_INCREMENT PRIMARY KEY,
  marca          VARCHAR(50) NOT NULL UNIQUE,
  ativo          BOOLEAN     NOT NULL DEFAULT TRUE,
  criado_em      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por     INT NULL,
  atualizado_em  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por INT NULL,
  CONSTRAINT fk_marcas_criado_por     FOREIGN KEY (criado_por)     REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_marcas_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE unidades_medida (
  id             INT        AUTO_INCREMENT PRIMARY KEY,
  unidade_medida VARCHAR(6) NOT NULL UNIQUE,
  descricao      VARCHAR(50) NOT NULL DEFAULT '',
  ativo          BOOLEAN    NOT NULL DEFAULT TRUE,
  criado_em      DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por     INT NULL,
  atualizado_em  DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por INT NULL,
  CONSTRAINT fk_unidades_criado_por     FOREIGN KEY (criado_por)     REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_unidades_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 5. CORES E TAMANHOS
-- ================================================================
CREATE TABLE cores (
  id        INT         AUTO_INCREMENT PRIMARY KEY,
  nome      VARCHAR(30) NOT NULL UNIQUE,
  ativo     TINYINT(1)  NOT NULL DEFAULT 1,
  criado_em DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE tamanhos (
  id        INT         AUTO_INCREMENT PRIMARY KEY,
  nome      VARCHAR(10) NOT NULL UNIQUE,
  ordem     INT         NOT NULL DEFAULT 99,
  ativo     TINYINT(1)  NOT NULL DEFAULT 1,
  criado_em DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ================================================================
-- 6. PESSOAS (Clientes e Emitentes)
-- ================================================================
CREATE TABLE clientes (
  id                    INT              AUTO_INCREMENT PRIMARY KEY,
  nome_razaosocial      VARCHAR(100)     NOT NULL,
  cpf_cnpj              VARCHAR(14)      NULL UNIQUE,
  tipo_pessoa           ENUM('PF','PJ')  NOT NULL DEFAULT 'PF',
  sexo                  ENUM('MASCULINO','FEMININO','OUTRO','NAO_INFORMAR')
                        NOT NULL DEFAULT 'NAO_INFORMAR',
  estrangeiro           BOOLEAN          NOT NULL DEFAULT FALSE,
  documento_estrangeiro VARCHAR(30)      NULL,
  apelido_nomefantasia  VARCHAR(100),
  cidade_id             INT NULL,
  endereco              VARCHAR(50),
  numero                VARCHAR(10),
  complemento           VARCHAR(50),
  bairro                VARCHAR(60),
  cep                   VARCHAR(9)       NULL COMMENT 'CEP no formato 00000-000',
  telefone              VARCHAR(15),
  celular               VARCHAR(15),
  email                 VARCHAR(100),
  inscricao_estadual    VARCHAR(20),
  inscricao_municipal   VARCHAR(20),
  limite_credito        DECIMAL(14,2)    NOT NULL DEFAULT 0,
  ativo                 BOOLEAN          NOT NULL DEFAULT TRUE,
  criado_em             DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por            INT NULL,
  atualizado_em         DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por        INT NULL,
  CONSTRAINT fk_clientes_cidade
    FOREIGN KEY (cidade_id) REFERENCES cidades(id) ON DELETE SET NULL,
  CONSTRAINT fk_clientes_criado_por
    FOREIGN KEY (criado_por) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_clientes_atualizado_por
    FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE emitentes (
  id                   INT          AUTO_INCREMENT PRIMARY KEY,
  nome_razaosocial     VARCHAR(100) NOT NULL,
  cnpj                 VARCHAR(14)  NOT NULL UNIQUE,
  apelido_nomefantasia VARCHAR(100),
  cidade_id            INT NULL,
  endereco             VARCHAR(50),
  numero               VARCHAR(10),
  complemento          VARCHAR(50),
  bairro               VARCHAR(50),
  cep                  VARCHAR(9)   NULL COMMENT 'CEP no formato 00000-000',
  telefone             VARCHAR(15),
  email                VARCHAR(50),
  inscricao_estadual   VARCHAR(20),
  inscricao_municipal  VARCHAR(20),
  regime_tributario    ENUM('SIMPLES','PRESUMIDO','REAL') NOT NULL DEFAULT 'SIMPLES',
  ativo                BOOLEAN      NOT NULL DEFAULT TRUE,
  criado_em            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por           INT NULL,
  atualizado_em        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por       INT NULL,
  CONSTRAINT fk_emitentes_cidade         FOREIGN KEY (cidade_id)      REFERENCES cidades(id)  ON DELETE SET NULL,
  CONSTRAINT fk_emitentes_criado_por     FOREIGN KEY (criado_por)     REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_emitentes_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 7. TRANSPORTES
-- ================================================================
CREATE TABLE transportadoras (
  id                 INT          AUTO_INCREMENT PRIMARY KEY,
  razaosocial        VARCHAR(100) NOT NULL UNIQUE,
  nomefantasia       VARCHAR(100) NULL,
  cnpj               VARCHAR(14)  NOT NULL UNIQUE,
  inscricao_estadual VARCHAR(20)  NULL,
  cidade_id          INT          NULL,
  endereco           VARCHAR(100) NULL,
  numero             VARCHAR(10),
  complemento        VARCHAR(50)  NULL,
  bairro             VARCHAR(60)  NULL,
  cep                VARCHAR(9)   NULL COMMENT 'CEP no formato 00000-000',
  telefone           VARCHAR(15)  NULL,
  email              VARCHAR(50)  NULL,
  ativo              BOOLEAN      NOT NULL DEFAULT TRUE,
  criado_em          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por         INT NULL,
  atualizado_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por     INT NULL,
  CONSTRAINT fk_transp_cidade
    FOREIGN KEY (cidade_id) REFERENCES cidades(id) ON DELETE SET NULL,
  CONSTRAINT fk_transp_criado_por
    FOREIGN KEY (criado_por) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_transp_atualizado_por
    FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE veiculos (
  id                INT        AUTO_INCREMENT PRIMARY KEY,
  transportadora_id INT        NOT NULL,
  placa             VARCHAR(7) NOT NULL UNIQUE,
  uf                CHAR(2)    NOT NULL,
  ativo             BOOLEAN    NOT NULL DEFAULT TRUE,
  criado_em         DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por        INT NULL,
  atualizado_em     DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por    INT NULL,
  CONSTRAINT fk_veiculos_transportadora   FOREIGN KEY (transportadora_id) REFERENCES transportadoras(id) ON DELETE NO ACTION,
  CONSTRAINT fk_veiculos_criado_por       FOREIGN KEY (criado_por)        REFERENCES usuarios(id)        ON DELETE SET NULL,
  CONSTRAINT fk_veiculos_atualizado_por   FOREIGN KEY (atualizado_por)    REFERENCES usuarios(id)        ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 8. FINANCEIRO BASE
-- ================================================================
CREATE TABLE metodos_pagamento (
  id               INT         AUTO_INCREMENT PRIMARY KEY,
  codigo           VARCHAR(4)  NOT NULL UNIQUE,
  metodo_pagamento VARCHAR(25) NOT NULL UNIQUE,
  ativo            BOOLEAN     NOT NULL DEFAULT TRUE,
  criado_em        DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por       INT NULL,
  atualizado_em    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por   INT NULL,
  CONSTRAINT fk_metodos_criado_por     FOREIGN KEY (criado_por)     REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_metodos_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE condicoes_pagamentos (
  id                        INT          AUTO_INCREMENT PRIMARY KEY,
  condicao_pagamento        VARCHAR(50)  NOT NULL UNIQUE,
  metodo_pagamento_id       INT          NOT NULL,
  numero_parcelas           INT          NOT NULL DEFAULT 1,
  entrada_minima_percentual DECIMAL(7,4) NOT NULL DEFAULT 0,
  desconto_percentual       DECIMAL(7,4) NOT NULL DEFAULT 0,
  acrescimo_percentual      DECIMAL(7,4) NOT NULL DEFAULT 0,
  multa_percentual          DECIMAL(7,4) NOT NULL DEFAULT 0,
  taxa_juros_percentual     DECIMAL(7,4) NOT NULL DEFAULT 0,
  ativo                     BOOLEAN      NOT NULL DEFAULT TRUE,
  criado_em                 DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por                INT NULL,
  atualizado_em             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por            INT NULL,
  CONSTRAINT fk_condicoes_metodo         FOREIGN KEY (metodo_pagamento_id) REFERENCES metodos_pagamento(id) ON DELETE NO ACTION,
  CONSTRAINT fk_condicoes_criado_por     FOREIGN KEY (criado_por)          REFERENCES usuarios(id)          ON DELETE SET NULL,
  CONSTRAINT fk_condicoes_atualizado_por FOREIGN KEY (atualizado_por)      REFERENCES usuarios(id)          ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE condicoes_pagamentos_parcelas (
  id                    INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  condicao_pagamento_id INT NOT NULL,
  numero_parcela        INT NOT NULL,
  dias_vencimento       INT NOT NULL DEFAULT 30,
  CONSTRAINT fk_cp_parcelas_condicao
    FOREIGN KEY (condicao_pagamento_id)
    REFERENCES condicoes_pagamentos(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ================================================================
-- 9. PRODUTOS
-- ================================================================
-- Custo NÃO fica no produto: é por variação e vem da última compra lançada
-- (produto_variacoes.preco_custo, calculado pelo módulo de Compras).
CREATE TABLE produtos (
  id                INT          AUTO_INCREMENT PRIMARY KEY,
  produto           VARCHAR(100) NOT NULL,
  descricao         VARCHAR(500),
  codigo_barras     VARCHAR(50) NULL,
  categoria_id      INT          NOT NULL,
  marca_id          INT          NOT NULL,
  unidade_medida_id INT          NOT NULL,
  ativo             BOOLEAN      NOT NULL DEFAULT TRUE,
  criado_em         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por        INT NULL,
  atualizado_em     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por    INT NULL,
  CONSTRAINT fk_produtos_categoria     FOREIGN KEY (categoria_id)      REFERENCES categorias(id)      ON DELETE NO ACTION,
  CONSTRAINT fk_produtos_marca         FOREIGN KEY (marca_id)          REFERENCES marcas(id)          ON DELETE NO ACTION,
  CONSTRAINT fk_produtos_unidade       FOREIGN KEY (unidade_medida_id) REFERENCES unidades_medida(id) ON DELETE NO ACTION,
  CONSTRAINT fk_produtos_criado_por    FOREIGN KEY (criado_por)        REFERENCES usuarios(id)        ON DELETE SET NULL,
  CONSTRAINT fk_produtos_atualizado_por FOREIGN KEY (atualizado_por)   REFERENCES usuarios(id)        ON DELETE SET NULL,
  UNIQUE KEY uq_produtos_codigo_barras (codigo_barras)
) ENGINE=InnoDB;

CREATE TABLE produto_variacoes (
  id                 INT           AUTO_INCREMENT PRIMARY KEY,
  produto_id         INT           NOT NULL,
  cor                VARCHAR(30)   NOT NULL,
  cor_id             INT           NULL,
  tamanho            VARCHAR(10)   NOT NULL,
  tamanho_id         INT           NULL,
  codigo_barras      VARCHAR(50)   UNIQUE,
  preco              DECIMAL(14,2) NOT NULL,
  -- Somente leitura para o cadastro: custo efetivo e data da última compra LANCADO
  -- (recalculados pelo módulo de Compras ao lançar/cancelar)
  preco_custo        DECIMAL(14,2) NOT NULL DEFAULT 0.00,
  data_ultima_compra DATE          NULL,
  ativo              BOOLEAN       NOT NULL DEFAULT TRUE,
  criado_em          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por         INT NULL,
  atualizado_em      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por     INT NULL,
  CONSTRAINT fk_variacoes_produto        FOREIGN KEY (produto_id)   REFERENCES produtos(id)   ON DELETE NO ACTION,
  CONSTRAINT fk_variacao_cor             FOREIGN KEY (cor_id)        REFERENCES cores(id)     ON DELETE SET NULL,
  CONSTRAINT fk_variacao_tamanho         FOREIGN KEY (tamanho_id)    REFERENCES tamanhos(id)  ON DELETE SET NULL,
  CONSTRAINT fk_variacoes_criado_por     FOREIGN KEY (criado_por)    REFERENCES usuarios(id)  ON DELETE SET NULL,
  CONSTRAINT fk_variacoes_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT unique_variacao             UNIQUE (produto_id, cor, tamanho)
) ENGINE=InnoDB;

CREATE TABLE estoque (
  id                  INT      AUTO_INCREMENT PRIMARY KEY,
  produto_variacao_id INT      NOT NULL UNIQUE,
  quantidade          INT      NOT NULL DEFAULT 0,
  atualizado_em       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por      INT NULL,
  CONSTRAINT fk_estoque_variacao        FOREIGN KEY (produto_variacao_id) REFERENCES produto_variacoes(id) ON DELETE NO ACTION,
  CONSTRAINT fk_estoque_atualizado_por  FOREIGN KEY (atualizado_por)      REFERENCES usuarios(id)          ON DELETE SET NULL
) ENGINE=InnoDB;

-- ================================================================
-- 10. MOVIMENTAÇÕES DE ESTOQUE
-- ================================================================
-- ENTRADA: lançamento de Compra (compra_id) ou estorno do cancelamento de Venda finalizada (venda_id).
-- SAIDA:   manual, pela finalização de Venda (venda_id) ou estorno do cancelamento de Compra (compra_id).
-- AJUSTE:  manual (inventário). Não altera custo nem data da última compra.
-- A tabela compras é criada depois (seção 11.1), por isso a FK de compra_id
-- é adicionada no final do script.
CREATE TABLE movimentacoes_estoque (
  id                INT          AUTO_INCREMENT PRIMARY KEY,
  tipo_movimentacao ENUM('ENTRADA','SAIDA','AJUSTE') NOT NULL,
  observacao        VARCHAR(200) NULL,
  compra_id         INT          NULL,
  venda_id          INT          NULL,
  criado_em         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por        INT NULL,
  CONSTRAINT fk_movest_criado_por  FOREIGN KEY (criado_por)    REFERENCES usuarios(id)     ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE movimentacoes_estoque_itens (
  id                  INT           AUTO_INCREMENT PRIMARY KEY,
  movimentacao_id     INT           NOT NULL,
  produto_variacao_id INT           NOT NULL,
  quantidade          INT           NOT NULL,
  sentido             ENUM('E','S') NULL,
  valor_unitario      DECIMAL(14,4) NOT NULL DEFAULT 0,
  criado_em           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_movest_itens_mov      FOREIGN KEY (movimentacao_id)     REFERENCES movimentacoes_estoque(id) ON DELETE NO ACTION,
  CONSTRAINT fk_movest_itens_variacao FOREIGN KEY (produto_variacao_id) REFERENCES produto_variacoes(id)    ON DELETE NO ACTION,
  CONSTRAINT chk_quantidade_positiva  CHECK (quantidade > 0)
) ENGINE=InnoDB;

-- ================================================================
-- 11. VENDAS
-- ================================================================
CREATE TABLE vendas (
  id                    INT           AUTO_INCREMENT PRIMARY KEY,
  emitente_id           INT NULL,
  cliente_id            INT NULL,
  movimentacao_id       INT NULL      UNIQUE,
  nfe_id                INT NULL      UNIQUE,
  condicao_pagamento_id INT NULL,
  valor_subtotal        DECIMAL(14,2) NOT NULL DEFAULT 0,
  desconto_percentual_aplicado DECIMAL(7,4) NOT NULL DEFAULT 0,
  valor_desconto        DECIMAL(14,2) NOT NULL DEFAULT 0,
  valor_total           DECIMAL(14,2) NOT NULL DEFAULT 0,
  status_venda          ENUM('ABERTA','FINALIZADA','CANCELADA') NOT NULL DEFAULT 'ABERTA',
  motivo_cancelamento   VARCHAR(255)  NULL,
  criado_em             DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por            INT NULL,
  atualizado_em         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por        INT NULL,
  CONSTRAINT fk_vendas_emitente       FOREIGN KEY (emitente_id)           REFERENCES emitentes(id)             ON DELETE SET NULL,
  CONSTRAINT fk_vendas_cliente        FOREIGN KEY (cliente_id)            REFERENCES clientes(id)              ON DELETE SET NULL,
  CONSTRAINT fk_vendas_movimentacao   FOREIGN KEY (movimentacao_id)       REFERENCES movimentacoes_estoque(id) ON DELETE SET NULL,
  CONSTRAINT fk_vendas_condicao       FOREIGN KEY (condicao_pagamento_id) REFERENCES condicoes_pagamentos(id)  ON DELETE SET NULL,
  CONSTRAINT fk_vendas_criado_por     FOREIGN KEY (criado_por)            REFERENCES usuarios(id)              ON DELETE SET NULL,
  CONSTRAINT fk_vendas_atualizado_por FOREIGN KEY (atualizado_por)        REFERENCES usuarios(id)              ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE vendas_itens (
  id                  INT           AUTO_INCREMENT PRIMARY KEY,
  venda_id            INT           NOT NULL,
  produto_variacao_id INT           NOT NULL,
  quantidade          INT           NOT NULL,
  valor_unitario      DECIMAL(14,2) NOT NULL,
  valor_desconto      DECIMAL(14,2) NOT NULL DEFAULT 0,
  valor_total         DECIMAL(14,2) NOT NULL,
  criado_em           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_vendas_itens_venda    FOREIGN KEY (venda_id)            REFERENCES vendas(id)            ON DELETE NO ACTION,
  CONSTRAINT fk_vendas_itens_variacao FOREIGN KEY (produto_variacao_id) REFERENCES produto_variacoes(id) ON DELETE NO ACTION,
  CONSTRAINT chk_qtd_venda_positiva   CHECK (quantidade > 0)
) ENGINE=InnoDB;

-- ================================================================
-- 11.1 COMPRAS
-- ================================================================
CREATE TABLE compras (
  id                      INT           AUTO_INCREMENT PRIMARY KEY,
  fornecedor_id           INT NULL,
  transportadora_id       INT NULL,
  numero_nf               VARCHAR(60)   NULL,
  modelo_nf               CHAR(2)       NULL,
  serie_nf                SMALLINT      NULL,
  chave_acesso            CHAR(44)      NULL,
  data_emissao            DATE          NOT NULL,
  data_chegada            DATE          NOT NULL,
  condicao_pagamento_id   INT NULL,
  valor_subtotal          DECIMAL(14,2) NOT NULL DEFAULT 0,
  valor_frete             DECIMAL(14,2) NOT NULL DEFAULT 0,
  valor_seguro            DECIMAL(14,2) NOT NULL DEFAULT 0,
  valor_outros_acrescimos DECIMAL(14,2) NOT NULL DEFAULT 0,
  valor_desconto          DECIMAL(14,2) NOT NULL DEFAULT 0,
  valor_total             DECIMAL(14,2) NOT NULL DEFAULT 0,
  status_compra           ENUM('LANCADO','CANCELADO') NOT NULL DEFAULT 'LANCADO',
  motivo_cancelamento     VARCHAR(255)  NULL,
  criado_em               DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por              INT NULL,
  atualizado_em           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por          INT NULL,
  CONSTRAINT fk_compras_fornecedor     FOREIGN KEY (fornecedor_id)         REFERENCES fornecedores(id)          ON DELETE SET NULL,
  CONSTRAINT fk_compras_transportadora FOREIGN KEY (transportadora_id)     REFERENCES transportadoras(id)       ON DELETE SET NULL,
  CONSTRAINT fk_compras_condicao       FOREIGN KEY (condicao_pagamento_id) REFERENCES condicoes_pagamentos(id)  ON DELETE SET NULL,
  CONSTRAINT fk_compras_criado_por     FOREIGN KEY (criado_por)            REFERENCES usuarios(id)              ON DELETE SET NULL,
  CONSTRAINT fk_compras_atualizado_por FOREIGN KEY (atualizado_por)        REFERENCES usuarios(id)              ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE compras_itens (
  id                     INT           AUTO_INCREMENT PRIMARY KEY,
  compra_id              INT           NOT NULL,
  produto_variacao_id    INT           NOT NULL,
  quantidade             INT           NOT NULL,
  valor_unitario         DECIMAL(14,4) NOT NULL,
  -- Desconto por unidade (fonte da verdade); valor_desconto = ROUND(quantidade * desconto_unitario, 2)
  desconto_unitario      DECIMAL(14,4) NOT NULL DEFAULT 0,
  valor_desconto         DECIMAL(14,2) NOT NULL DEFAULT 0,
  desconto_percentual    DECIMAL(7,4)  NOT NULL DEFAULT 0,
  valor_total            DECIMAL(14,2) NOT NULL,
  -- Custo por unidade: valor líquido do item + rateio de frete/outros acréscimos (proporcional ao valor)
  custo_unitario_efetivo DECIMAL(14,4) NOT NULL DEFAULT 0,
  criado_em              DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_compras_itens_compra   FOREIGN KEY (compra_id)           REFERENCES compras(id)           ON DELETE NO ACTION,
  CONSTRAINT fk_compras_itens_variacao FOREIGN KEY (produto_variacao_id) REFERENCES produto_variacoes(id) ON DELETE NO ACTION,
  CONSTRAINT chk_qtd_compra_positiva   CHECK (quantidade > 0)
) ENGINE=InnoDB;

-- ================================================================
-- 12. NF-e (saída de venda e entrada de devolução)
-- ================================================================
CREATE TABLE nfes (
  id                INT           AUTO_INCREMENT PRIMARY KEY,
  chave_acesso      VARCHAR(44)   UNIQUE,
  numero            INT           NOT NULL,
  serie             SMALLINT      NOT NULL DEFAULT 1,
  data_emissao      DATETIME      NOT NULL,
  data_saida        DATETIME,
  emitente_id       INT           NOT NULL,
  cliente_id        INT           NOT NULL,
  venda_id          INT NULL      UNIQUE,
  transportadora_id INT NULL,
  tipo_operacao     ENUM('SAIDA','ENTRADA') NOT NULL DEFAULT 'SAIDA',
  finalidade        ENUM('NORMAL','DEVOLUCAO') NOT NULL DEFAULT 'NORMAL',
  nfe_referenciada_id INT NULL,
  cfop              CHAR(4)       NULL,
  natureza_operacao VARCHAR(60)   NULL,
  status_nfe        ENUM('RASCUNHO','EMITIDA','CANCELADA') NOT NULL DEFAULT 'RASCUNHO',
  motivo_cancelamento VARCHAR(255) NULL,
  valor_produtos    DECIMAL(14,2) NOT NULL DEFAULT 0,
  valor_desconto    DECIMAL(14,2) NOT NULL DEFAULT 0,
  valor_total       DECIMAL(14,2) NOT NULL DEFAULT 0,
  criado_em         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por        INT NULL,
  atualizado_em     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por    INT NULL,
  CONSTRAINT fk_nfes_emitente         FOREIGN KEY (emitente_id)       REFERENCES emitentes(id)       ON DELETE NO ACTION,
  CONSTRAINT fk_nfes_cliente          FOREIGN KEY (cliente_id)        REFERENCES clientes(id)        ON DELETE NO ACTION,
  CONSTRAINT fk_nfes_venda            FOREIGN KEY (venda_id)          REFERENCES vendas(id)          ON DELETE SET NULL,
  CONSTRAINT fk_nfes_transportadora   FOREIGN KEY (transportadora_id) REFERENCES transportadoras(id) ON DELETE SET NULL,
  CONSTRAINT fk_nfes_referenciada     FOREIGN KEY (nfe_referenciada_id) REFERENCES nfes(id)        ON DELETE NO ACTION,
  CONSTRAINT fk_nfes_criado_por       FOREIGN KEY (criado_por)        REFERENCES usuarios(id)        ON DELETE SET NULL,
  CONSTRAINT fk_nfes_atualizado_por   FOREIGN KEY (atualizado_por)    REFERENCES usuarios(id)        ON DELETE SET NULL,
  CONSTRAINT unique_nfe               UNIQUE (emitente_id, serie, numero)
) ENGINE=InnoDB;

CREATE TABLE nfes_produtos (
  id                  INT           AUTO_INCREMENT PRIMARY KEY,
  nfe_id              INT           NOT NULL,
  numero_item         INT           NOT NULL,
  produto_variacao_id INT           NOT NULL,
  descricao_item      VARCHAR(100)  NOT NULL,
  unidade_medida_id   INT           NOT NULL,
  quantidade          DECIMAL(14,4) NOT NULL,
  valor_unitario      DECIMAL(14,4) NOT NULL,
  valor_desconto      DECIMAL(14,4) NOT NULL DEFAULT 0,
  valor_total         DECIMAL(14,4) NOT NULL,
  criado_em           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_nfes_prod_nfe      FOREIGN KEY (nfe_id)              REFERENCES nfes(id)              ON DELETE NO ACTION,
  CONSTRAINT fk_nfes_prod_variacao FOREIGN KEY (produto_variacao_id) REFERENCES produto_variacoes(id) ON DELETE NO ACTION,
  CONSTRAINT fk_nfes_prod_unidade  FOREIGN KEY (unidade_medida_id)   REFERENCES unidades_medida(id)   ON DELETE NO ACTION,
  CONSTRAINT unique_nfe_item       UNIQUE (nfe_id, numero_item)
) ENGINE=InnoDB;

-- ================================================================
-- 14. CONTAS
-- ================================================================
CREATE TABLE contas_pagar (
  id              INT           AUTO_INCREMENT PRIMARY KEY,
  fornecedor_id   INT NULL,
  compra_id       INT NULL,
  cliente_id      INT NULL,
  venda_id        INT NULL,
  descricao       VARCHAR(150) NOT NULL,
  data_vencimento DATE          NOT NULL,
  data_pagamento  DATE               NULL,
  comprovante_arquivo VARCHAR(255) NULL,
  valor_original  DECIMAL(14,2) NOT NULL,
  valor_saldo     DECIMAL(14,2) NOT NULL,
  status          ENUM('ABERTA','PAGA','CANCELADA') NOT NULL DEFAULT 'ABERTA',
  criado_em       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por      INT NULL,
  atualizado_em   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por  INT NULL,
  CONSTRAINT fk_cpagar_fornecedor     FOREIGN KEY (fornecedor_id)   REFERENCES fornecedores(id)  ON DELETE SET NULL,
  CONSTRAINT fk_cpagar_compra         FOREIGN KEY (compra_id)       REFERENCES compras(id)       ON DELETE SET NULL,
  CONSTRAINT fk_cpagar_cliente        FOREIGN KEY (cliente_id)      REFERENCES clientes(id)      ON DELETE SET NULL,
  CONSTRAINT fk_cpagar_venda          FOREIGN KEY (venda_id)        REFERENCES vendas(id)        ON DELETE SET NULL,
  CONSTRAINT fk_cpagar_criado_por     FOREIGN KEY (criado_por)      REFERENCES usuarios(id)      ON DELETE SET NULL,
  CONSTRAINT fk_cpagar_atualizado_por FOREIGN KEY (atualizado_por)  REFERENCES usuarios(id)      ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE contas_receber (
  id              INT           AUTO_INCREMENT PRIMARY KEY,
  cliente_id      INT           NOT NULL,
  venda_id        INT NULL,
  nfe_id          INT NULL,
  descricao       VARCHAR(100),
  data_vencimento DATE          NOT NULL,
  valor_original  DECIMAL(14,2) NOT NULL,
  valor_saldo     DECIMAL(14,2) NOT NULL,
  status          ENUM('ABERTA','RECEBIDA','CANCELADA') NOT NULL DEFAULT 'ABERTA',
  criado_em       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por      INT NULL,
  atualizado_em   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  atualizado_por  INT NULL,
  CONSTRAINT fk_creceber_cliente        FOREIGN KEY (cliente_id)     REFERENCES clientes(id)  ON DELETE NO ACTION,
  CONSTRAINT fk_creceber_venda          FOREIGN KEY (venda_id)       REFERENCES vendas(id)    ON DELETE SET NULL,
  CONSTRAINT fk_creceber_nfe            FOREIGN KEY (nfe_id)         REFERENCES nfes(id)      ON DELETE SET NULL,
  CONSTRAINT fk_creceber_criado_por     FOREIGN KEY (criado_por)     REFERENCES usuarios(id)  ON DELETE SET NULL,
  CONSTRAINT fk_creceber_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios(id)  ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE contas_receber_baixas (
  id               INT           AUTO_INCREMENT PRIMARY KEY,
  conta_receber_id INT           NOT NULL,
  data_recebimento DATE          NOT NULL,
  valor_recebido   DECIMAL(14,2) NOT NULL,
  comprovante_arquivo VARCHAR(255) NULL,
  observacao       VARCHAR(150)  NULL,
  criado_em        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  criado_por       INT NULL,
  CONSTRAINT fk_crbaixas_conta      FOREIGN KEY (conta_receber_id) REFERENCES contas_receber(id) ON DELETE CASCADE,
  CONSTRAINT fk_crbaixas_criado_por FOREIGN KEY (criado_por)       REFERENCES usuarios(id)        ON DELETE SET NULL,
  CONSTRAINT chk_crbaixas_valor_positivo CHECK (valor_recebido > 0)
) ENGINE=InnoDB;

-- ================================================================
-- FKs adicionadas após a criação das tabelas referenciadas
-- ================================================================
ALTER TABLE movimentacoes_estoque
  ADD CONSTRAINT fk_movest_compra FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE SET NULL,
  ADD CONSTRAINT fk_movest_venda  FOREIGN KEY (venda_id)  REFERENCES vendas(id)  ON DELETE SET NULL;

ALTER TABLE fornecedores
  ADD CONSTRAINT fk_fornecedores_condicao FOREIGN KEY (condicao_pagamento_id) REFERENCES condicoes_pagamentos(id) ON DELETE SET NULL;

ALTER TABLE vendas
  ADD CONSTRAINT fk_vendas_nfe FOREIGN KEY (nfe_id) REFERENCES nfes(id) ON DELETE SET NULL;