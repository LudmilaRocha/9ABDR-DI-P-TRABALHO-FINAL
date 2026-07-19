# Snowflake | World Cup (alinhado ao Databricks)

Pipeline Medallion no Snowflake (Membro 3 - Ayrton).

Pergunta de negocio ([FOUNDATION.md](../FOUNDATION.md)): o time reage depois de sofrer um gol?

Fonte e regras iguais ao pipeline em `databricks/`: **openfootball/worldcup.json**.

## Estrutura

| Arquivo / pasta | Conteudo |
|-----------------|----------|
| `00_download_flatten_worldcup.py` | Download ZIP worldcup.json + CSVs flat |
| `00_PROPOSTA_BASE_E_ALINHAMENTO.md` | Escopo Snowflake |
| `01` a `07` `*.sql` | Setup, Bronze, Silver, Gold, QC, Task, Streamlit |
| `dbt_openfootball/` | Models e testes dbt |
| `streamlit_in_snowflake/` | App Streamlit no Snowflake |
| `run_snowflake_sql.py` / `load_env.ps1` | Execucao via CLI |

## Dados

- Repositorio: `openfootball/worldcup.json` (ZIP master)
- Filtro: `name` contem `World Cup` e nao contem `Club`
- Extração: full do ZIP a cada run (sem janela de datas no codigo)
- Janela operacional: semanal (segunda 06:00); diario opcional em ano de Copa

## Fluxo

```
worldcup.json (ZIP)
  -> BRONZE.MATCHES (MERGE) / BRONZE.GOALS_RAW (overwrite)
  -> SILVER.MATCHES / GOAL_EVENTS (+ quarantine)
  -> GOLD.FACT_REACTION_EVENTS
  -> GOLD.DIM_COMPETITION_SUMMARY

QC: checks SQL + dbt test
Schedule: PIPE.TASK_WORLDCUP_WEEKLY (segunda 06:00 America/Sao_Paulo)
Consumo: Streamlit GOLD.WORLDCUP_GOLD_DASH
```

## Regras alinhadas ao Databricks

- `match_id = MD5(match_date_team_home_team_away)`
- `credited_team = team`, `conceding_team = opponent` (gol contra nao inverte)
- Gold agrega por `competition_name`
- Quarentena: `PARTIDA_INVALIDA` / `EVENTO_GOL_INVALIDO`

## Como rodar no Snowflake

1. Copie `.env.example` para `.env` e preencha conta, usuario e PAT/senha.
2. Se o CLI reclamar de IP bloqueado, crie/atualize a network policy no Snowsight (ACCOUNTADMIN) com o IP publico da maquina.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python 00_download_flatten_worldcup.py
python run_snowflake_sql.py 01_setup_snowflake.sql
python run_snowflake_sql.py --put-data-flat
python run_snowflake_sql.py 02_bronze_ingest.sql
python run_snowflake_sql.py 03_silver_transform.sql
python run_snowflake_sql.py 04_gold_insights.sql
python run_snowflake_sql.py 05_quality_checks.sql
python run_snowflake_sql.py 06_pipeline_procedures_and_schedule.sql
python run_snowflake_sql.py 07_streamlit_in_snowflake.sql
# PUT do streamlit_in_snowflake/* no stage GOLD.STG_STREAMLIT_APP
```

dbt:

```powershell
.\load_env.ps1
copy .\dbt_openfootball\profiles.yml.example .\dbt_openfootball\profiles.yml
cd dbt_openfootball
dbt deps
dbt run
dbt test
```

Disparar o job:

```sql
EXECUTE TASK PIPE.TASK_WORLDCUP_WEEKLY;
```

Consultas:

```sql
SELECT * FROM GOLD.DIM_COMPETITION_SUMMARY ORDER BY COMPETITION_NAME;
SELECT * FROM GOLD.FACT_REACTION_EVENTS
ORDER BY MATCH_DATE, GOAL_MINUTE
LIMIT 50;
```
