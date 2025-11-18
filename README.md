# ⚽ Efficiency Fin Soccer

Pipeline de extração e análise de dados de futebol integrando API-Football com infraestrutura AWS.

## 🎯 Visão Geral

Sistema que extrai dados da API-Football (fixtures, artilheiros e assistências), armazena em S3 com estrutura particionada, carrega em PostgreSQL RDS e cataloga via AWS Glue para consultas no Athena.

**Fluxo:** API-Football → CSV Local → S3 + PostgreSQL → Glue Crawler → Athena

## 📁 Estrutura

```text
├── main.py                     # Entry point do pipeline
├── config/config.json          # Configuração de seasons/leagues
├── data/
│   ├── sql/schema.sql          # Schema PostgreSQL (fonte única)
│   ├── sport/                  # CSVs extraídos (seasons, players)
│   └── financial/              # Dados financeiros (futuro)
├── src/libs/
│   ├── api_football.py         # Client e services da API
│   ├── api_football_models.py  # Modelos Pydantic
│   ├── pipeline.py             # Orquestrador do pipeline
│   └── storage.py              # S3, PostgreSQL e Glue
├── docs/api/                   # Especificação OpenAPI
└── terraform/                  # Infraestrutura AWS (S3, RDS, VPC, Glue, Athena)
```

## 🔧 Componentes

**🐍 Python Pipeline:**

- Extração configurável por leagues/seasons (config.json)
- Upload S3 com limpeza automática e particionamento
- Carga PostgreSQL via COPY com tratamento de NULL
- Schema gerenciado em arquivo único (docs/sql/schema.sql)
- Execução de crawlers Glue
- Monitoramento de progresso com tqdm

**☁️ Infraestrutura AWS:**

- S3 Data Lake com lifecycle policies (STANDARD → STANDARD_IA @ 30d → GLACIER_IR @ 90d)
- RDS PostgreSQL 17.2 (db.t3.micro, 20GB gp3, sem backup)
- VPC com subnets públicas
- Glue Database + Crawlers
- Athena Workgroup

**📊 Dados:**

- Fixtures: Resultados de partidas (11 colunas + índices)
- Top Scorers: Artilheiros por liga/temporada/jogador (12 colunas)
- Top Assists: Assistências por liga/temporada/jogador (12 colunas)

## 🚀 Configuração

1. Instalar dependências: `uv sync`
2. Definir seasons/leagues em `config/config.json`
3. Provisionar infraestrutura: `cd terraform && terraform apply`
4. Configurar `.env` com outputs do Terraform + credenciais API
5. Executar pipeline completo: `uv run python main.py`
