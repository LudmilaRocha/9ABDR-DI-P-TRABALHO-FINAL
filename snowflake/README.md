# Snowflake | openfootball

Pipeline Medallion no Snowflake (Membro 3 - Ayrton).

Pergunta de negocio ([FOUNDATION.md](../FOUNDATION.md)): o time reage depois de sofrer um gol?

## Estrutura

| Arquivo / pasta | Conteudo |
|-----------------|----------|
| `00_download_flatten_openfootball.py` | Download da fonte e CSVs flat |
| `01` a `07` `*.sql` | Setup, Bronze, Silver, Gold, QC, Task, Streamlit |
| `dbt_openfootball/` | Models e testes dbt |
| `streamlit_in_snowflake/` | App Streamlit no Snowflake |
| `run_snowflake_sql.py` / `load_env.ps1` | Execucao via CLI |
| `00_PROPOSTA_BASE_E_ALINHAMENTO.md` | Escopo Snowflake |

## Dados

- Big 5 2023/24 (`football.json`): partidas (placar final)
- Copa do Mundo 2022 (`worldcup.more`): partidas + gols com minuto

A Gold de reacao usa a Copa (fonte com minuto).

## Fluxo

```
Fonte GitHub
  -> BRONZE.MATCHES_RAW / GOALS_RAW
  -> SILVER.MATCHES / GOAL_EVENTS (+ quarantine)
  -> GOLD.RESPONSE_AFTER_CONCEDING
  -> GOLD.LEAGUE_REACTION_SUMMARY

QC: checks SQL + dbt test (QC.DBT_RUN_RESULTS)
Schedule: PIPE.TASK_OPENFOOTBALL_WEEKLY (segunda 06:00 America/Sao_Paulo)
Consumo: Streamlit in Snowflake
```

## Como rodar

1. Copie `.env.example` para `.env` e preencha conta, usuario e PAT/senha.
2. PAT no Snowflake exige network policy no usuario/conta (configure no Snowsight antes do CLI).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python 00_download_flatten_openfootball.py
python run_snowflake_sql.py --put-data-flat
python run_snowflake_sql.py 01_setup_snowflake.sql
python run_snowflake_sql.py 02_bronze_ingest.sql
python run_snowflake_sql.py 03_silver_transform.sql
python run_snowflake_sql.py 04_gold_insights.sql
python run_snowflake_sql.py 05_quality_checks.sql
python run_snowflake_sql.py 06_pipeline_procedures_and_schedule.sql
python run_snowflake_sql.py 07_streamlit_in_snowflake.sql
# depois: PUT do streamlit_in_snowflake/streamlit_app.py no stage do app
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
EXECUTE TASK PIPE.TASK_OPENFOOTBALL_WEEKLY;
```

Consultas:

```sql
SELECT * FROM GOLD.LEAGUE_REACTION_SUMMARY;
SELECT * FROM GOLD.RESPONSE_AFTER_CONCEDING
ORDER BY MATCH_DATE, GOAL_MINUTE
LIMIT 50;
```
