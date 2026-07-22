╔══════════════════════════════════════════════════════════════════════════════════════╗
║         PIPELINE — OPEN FOOTBALL DATABASE  │  Arquitetura Medallion                ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────┐
│           FONTE  —  GitHub (openfootball)    │
│                                              │
│  football.json          *.txt por liga       │
│  (placar final por      (eventos de gol      │
│   rodada/temporada)      com minuto)         │
└──────────────────────────┬───────────────────┘
                           │  HTTP / Git pull
                           │  Semanal: seg 06h  |  Recesso: dia 1/mês 06h
                           ▼
══════════════════════════════════════════════════════════════════════════════════
  BRONZE  —  Dado bruto, sem transformação
══════════════════════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────┐     ┌─────────────────────────────────┐
  │         DATABRICKS              │     │          SNOWFLAKE              │
  │                                 │     │                                 │
  │  Ingestão:  PySpark notebook    │     │  Ingestão:  Snowpark (Python)   │
  │  Storage:   Delta Lake          │     │  Storage:   Internal Stage      │
  │  Catálogo:  Unity Catalog       │     │  Catálogo:  Snowflake DB/Schema │
  │  Orquest.:  Databricks Workflow │     │  Orquest.:  Snowflake Tasks     │
  │                                 │     │                                 │
  │  bronze.matches_raw             │     │  BRONZE.MATCHES_RAW             │
  │  bronze.goals_raw               │     │  BRONZE.GOALS_RAW               │
  └───────────────┬─────────────────┘     └─────────────────┬───────────────┘
                  └──────────────┬────────────────────────────┘
                                 ▼
              ┌──────────────────────────────────────────┐
              │  ✓  QUALITY CHECKS — Bronze              │
              │                                          │
              │  • Schema: campos obrigatórios presentes │
              │  • Not-null: date, team1, team2, score   │
              │  • Sem source_file duplicado na carga    │
              │  • Score não-negativo (≥ 0)              │
              │                                          │
              │  Falha → registro vai para _quarantine   │
              │           carga continua normalmente     │
              └──────────────────┬───────────────────────┘
                                 │
                                 ▼
══════════════════════════════════════════════════════════════════════════════════
  SILVER  —  Dado limpo, normalizado e enriquecido
══════════════════════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────┐     ┌─────────────────────────────────┐
  │         DATABRICKS              │     │          SNOWFLAKE              │
  │                                 │     │                                 │
  │  Transform.: PySpark + SQL      │     │  Transform.: Snowpark / SQL     │
  │  Formato:    Delta (ACID +      │     │  Formato:    Snowflake native   │
  │              time travel)       │     │              (ACID nativo)      │
  │  Schema evo: Unity Catalog      │     │  Schema evo: Schema Evolution   │
  │                                 │     │                                 │
  │  silver.matches                 │     │  SILVER.MATCHES                 │
  │  silver.goal_events             │     │  SILVER.GOAL_EVENTS             │
  └───────────────┬─────────────────┘     └─────────────────┬───────────────┘
                  └──────────────┬────────────────────────────┘
                                 ▼
              ┌──────────────────────────────────────────┐
              │  ✓  QUALITY CHECKS — Silver              │
              │                                          │
              │  • Integridade ref.: goal_event tem      │
              │    match_id válido em matches            │
              │  • Datas: date ∈ [1990-01-01, hoje]      │
              │  • Sanidade: soma dos gols nos eventos   │
              │    = score_ft_home / score_ft_away       │
              │  • Deduplicação: sem (date, team1, team2)│
              │    duplicado por liga/temporada          │
              │                                          │
              │  Falha → DQ report gerado                │
              │           registro tagueado: dq_issue=T  │
              └──────────────────┬───────────────────────┘
                                 │
                                 ▼
══════════════════════════════════════════════════════════════════════════════════
  GOLD  —  Métricas prontas para consumo
══════════════════════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────┐     ┌─────────────────────────────────┐
  │         DATABRICKS              │     │          SNOWFLAKE              │
  │                                 │     │                                 │
  │  Modelo:   SQL + PySpark        │     │  Modelo:   SQL / Dynamic Tables │
  │  Update:   MERGE INTO           │     │  Update:   MERGE / Stream-based │
  │  Exposição:Databricks SQL Wh.   │     │  Exposição:Snowflake Warehouse  │
  │                                 │     │            Streamlit in SF      │
  │                                 │     │                                 │
  │  gold.response_after_conceding  │     │  GOLD.RESPONSE_AFTER_CONCEDING  │
  │  gold.league_reaction_summary   │     │  GOLD.LEAGUE_REACTION_SUMMARY   │
  └───────────────┬─────────────────┘     └─────────────────┬───────────────┘
                  └──────────────┬────────────────────────────┘
                                 ▼
              ┌──────────────────────────────────────────┐
              │  ✓  QUALITY CHECKS — Gold                │
              │                                          │
              │  • Completude: toda liga/temporada ativa │
              │    tem registros na Gold                 │
              │  • Nenhum registro com dq_issue=T        │
              │    incluído nas métricas                 │
              │  • Total de partidas Gold ≥ Silver       │
              │                                          │
              │  Falha → Gold não é atualizada           │
              │           versão anterior permanece      │
              └──────────────────┬───────────────────────┘
                                 │
                                 ▼
              ┌──────────────────────────────────────────┐
              │     CONSUMO  —  Pergunta de negócio      │
              │                                          │
              │  "Qual % dos times reage após sofrer um  │
              │   gol? Esse padrão varia por liga?"      │
              │                                          │
              │  Dashboard  /  Query analítica           │
              └──────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════════
  FREQUÊNCIA DE EXECUÇÃO
══════════════════════════════════════════════════════════════════════════════════

  Período          Frequência     Cron                  Escopo
  ─────────────────────────────────────────────────────────────────────────
  Temporada        Semanal        0 6 * * 1 (UTC)       Bronze→Silver→Gold
  (ago – mai)      (toda seg)

  Recesso          Mensal         0 6 1 * * (UTC)       Verificação + Bronze
  (jun – jul)      (dia 1/mês)

  Correções        Sob demanda    manual                 Reprocessamento parcial
  ─────────────────────────────────────────────────────────────────────────
  Databricks:  Databricks Workflow  →  Job com cron schedule
  Snowflake:   Task raiz com        →  USING CRON 0 6 * * 1 UTC
               Task filhas encadeadas por AFTER (Silver depois Bronze, Gold depois Silver)