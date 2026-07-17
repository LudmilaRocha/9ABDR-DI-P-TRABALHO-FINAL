import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Resposta apos sofrer gol", layout="wide")
session = get_active_session()

st.title("Eficiencia emocional: resposta apos sofrer um gol")
st.caption("Gold RESPONSE_AFTER_CONCEDING | eventos com minuto: Copa 2022")

summary = session.sql(
    """
    SELECT LEAGUE, SEASON, CONCEDED_EVENTS, REACTED_EVENTS, PCT_REACTED,
           AVG_GOALS_AFTER_CONCEDING, PCT_ENDED_WIN
    FROM GOLD.LEAGUE_REACTION_SUMMARY
    ORDER BY LEAGUE, SEASON
    """
).to_pandas()

by_minute = session.sql(
    """
    SELECT
        CASE
            WHEN GOAL_MINUTE BETWEEN 1 AND 15 THEN '01-15'
            WHEN GOAL_MINUTE BETWEEN 16 AND 30 THEN '16-30'
            WHEN GOAL_MINUTE BETWEEN 31 AND 45 THEN '31-45'
            WHEN GOAL_MINUTE BETWEEN 46 AND 60 THEN '46-60'
            WHEN GOAL_MINUTE BETWEEN 61 AND 75 THEN '61-75'
            WHEN GOAL_MINUTE BETWEEN 76 AND 90 THEN '76-90'
            ELSE '90+'
        END AS FAIXA_MINUTO,
        COUNT(*) AS EVENTOS,
        ROUND(100.0 * AVG(REACTED_FLAG), 1) AS PCT_REAGIU,
        ROUND(AVG(GOALS_SCORED_AFTER_CONCEDING), 2) AS MEDIA_GOLS_DEPOIS
    FROM GOLD.RESPONSE_AFTER_CONCEDING
    GROUP BY 1
    ORDER BY 1
    """
).to_pandas()

by_result = session.sql(
    """
    SELECT FINAL_RESULT AS RESULTADO, COUNT(*) AS EVENTOS
    FROM GOLD.RESPONSE_AFTER_CONCEDING
    GROUP BY 1
    ORDER BY
        CASE FINAL_RESULT
            WHEN 'WIN' THEN 1
            WHEN 'DRAW' THEN 2
            WHEN 'LOSS' THEN 3
            ELSE 4
        END
    """
).to_pandas()

by_goals_after = session.sql(
    """
    SELECT
        GOALS_SCORED_AFTER_CONCEDING AS GOLS_DEPOIS,
        COUNT(*) AS EVENTOS
    FROM GOLD.RESPONSE_AFTER_CONCEDING
    GROUP BY 1
    ORDER BY 1
    """
).to_pandas()

detail = session.sql(
    """
    SELECT MATCH_DATE, CONCEDING_TEAM, SCORING_TEAM, SCORER, GOAL_MINUTE,
           SCORE_DIFF_BEFORE_GOAL, GOALS_SCORED_AFTER_CONCEDING,
           FINAL_RESULT, REACTED_FLAG
    FROM GOLD.RESPONSE_AFTER_CONCEDING
    ORDER BY MATCH_DATE, GOAL_MINUTE
    LIMIT 40
    """
).to_pandas()

checks = session.sql(
    """
    SELECT CHECKED_AT, CHECK_NAME, LAYER, STATUS, FAILED_ROWS, DETAILS
    FROM QC.CHECK_RESULTS
    ORDER BY CHECKED_AT DESC
    LIMIT 20
    """
).to_pandas()

if len(summary) == 0:
    st.warning("Gold vazia. Rode o pipeline / dbt run.")
    st.stop()

row = summary.iloc[0]
m1, m2, m3, m4 = st.columns(4)
m1.metric("Eventos de gol sofrido", int(row["CONCEDED_EVENTS"]))
m2.metric("% reagiu (marcou depois)", f"{row['PCT_REACTED']}%")
m3.metric("Media gols apos sofrer", float(row["AVG_GOALS_AFTER_CONCEDING"]))
m4.metric("% terminou em vitoria", f"{row['PCT_ENDED_WIN']}%")

st.divider()

g1, g2 = st.columns(2, gap="large")

with g1:
    st.subheader("% de reacao por faixa de minuto")
    if len(by_minute) > 1:
        chart_min = by_minute.set_index("FAIXA_MINUTO")[["PCT_REAGIU"]]
        st.line_chart(chart_min, height=280)
        st.dataframe(by_minute, use_container_width=True, hide_index=True)
    else:
        st.info("Poucos dados para agrupar por minuto.")

with g2:
    st.subheader("Gols marcados depois de sofrer")
    if len(by_goals_after) > 0:
        chart_g = by_goals_after.set_index("GOLS_DEPOIS")[["EVENTOS"]]
        st.bar_chart(chart_g, height=280)
        st.dataframe(by_goals_after, use_container_width=True, hide_index=True)

st.divider()

g3, g4 = st.columns(2, gap="large")

with g3:
    st.subheader("Resultado final do time que sofreu o gol")
    if len(by_result) > 0:
        chart_r = by_result.set_index("RESULTADO")[["EVENTOS"]]
        st.bar_chart(chart_r, height=260)
        st.dataframe(by_result, use_container_width=True, hide_index=True)

with g4:
    st.subheader("Resumo do torneio")
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.subheader("Amostra de eventos")
    st.dataframe(detail, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Quality checks (QC.CHECK_RESULTS)")
st.dataframe(checks, use_container_width=True, hide_index=True)
