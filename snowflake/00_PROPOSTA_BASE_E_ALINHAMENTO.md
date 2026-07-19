# Escopo Snowflake (worldcup.json)

Responsavel: Ayrton (Membro 3)

Base do grupo: [FOUNDATION.md](../FOUNDATION.md)

Pergunta: eficiencia emocional - o time reage depois de sofrer um gol?

Alinhado ao pipeline Databricks em `../databricks/`.

## Fonte

| Fonte | Uso |
|-------|-----|
| `openfootball/worldcup.json` (ZIP master) | Partidas + eventos de gol com minuto |

Filtro: competicoes com `World Cup` no nome, excluindo `Club`.

Extração full do ZIP a cada run. Janela operacional: semanal fora do torneio; diario durante a Copa.

## Camadas

| Camada | Objetos |
|--------|---------|
| Bronze | `MATCHES` (MERGE), `GOALS_RAW` (overwrite) |
| Silver | `MATCHES`, `GOAL_EVENTS` (+ quarantine) |
| Gold | `FACT_REACTION_EVENTS`, `DIM_COMPETITION_SUMMARY` |
| QC | `CHECK_RESULTS`, `PIPELINE_RUNS`, dbt tests |
| Schedule | `PIPE.TASK_WORLDCUP_WEEKLY` (semanal; diario opcional em ano de Copa) |
| Streamlit | `GOLD.WORLDCUP_GOLD_DASH` |

## Gold

Grain de `FACT_REACTION_EVENTS` = cada gol sofrido:

- `conceding_team`, `goal_minute`, `score_diff_before_goal`
- `goals_scored_after_conceding`
- `final_result` (WIN/DRAW/LOSS do time que sofreu)
- `reacted_flag` = 1 se marcou pelo menos 1 gol depois

`DIM_COMPETITION_SUMMARY` agrega por `competition_name`.

```sql
SELECT * FROM GOLD.DIM_COMPETITION_SUMMARY ORDER BY COMPETITION_NAME;
SELECT * FROM GOLD.FACT_REACTION_EVENTS
ORDER BY MATCH_DATE, GOAL_MINUTE LIMIT 50;
```
