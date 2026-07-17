# Escopo Snowflake (openfootball)

Responsavel: Ayrton (Membro 3)

Base do grupo: [FOUNDATION.md](../FOUNDATION.md)

Pergunta: eficiencia emocional - o time reage depois de sofrer um gol?

## Fontes

| Fonte | Uso |
|-------|-----|
| `football.json` Big 5 2023/24 | Partidas (placar final) em `BRONZE.MATCHES_RAW` |
| `worldcup.more` Copa 2022 TXT | Partidas + eventos de gol com minuto em `GOALS_RAW` |

Os TXT das ligas Big 5 nao trazem minuto. A metrica `goals_scored_after_conceding` e calculada na Copa 2022.

## Camadas

| Camada | Objetos |
|--------|---------|
| Bronze | `MATCHES_RAW`, `GOALS_RAW` |
| Silver | `MATCHES`, `GOAL_EVENTS` (+ quarantine) |
| Gold | `RESPONSE_AFTER_CONCEDING`, `LEAGUE_REACTION_SUMMARY` |
| QC | `CHECK_RESULTS`, `PIPELINE_RUNS`, dbt tests |
| Schedule | `PIPE.TASK_OPENFOOTBALL_WEEKLY` (cron `0 6 * * 1` America/Sao_Paulo) |

## Gold

Grain de `RESPONSE_AFTER_CONCEDING` = cada gol sofrido:

- `conceding_team`, `goal_minute`, `score_diff_before_goal`
- `goals_scored_after_conceding` (gols do time que sofreu, apos o minuto)
- `final_result` (WIN/DRAW/LOSS do time que sofreu)
- `REACTED_FLAG` = 1 se marcou pelo menos 1 gol depois

```sql
SELECT * FROM GOLD.LEAGUE_REACTION_SUMMARY;
SELECT * FROM GOLD.RESPONSE_AFTER_CONCEDING
ORDER BY MATCH_DATE, GOAL_MINUTE LIMIT 50;
```
