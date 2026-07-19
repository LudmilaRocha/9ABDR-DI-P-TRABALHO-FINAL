import re

import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Capacidade de reacao - Copas", layout="wide")
session = get_active_session()

st.title("Capacidade de reacao vs viradas em Copas do Mundo")
st.caption(
    "Pergunta (igual Databricks): qual % das selecoes reage apos sofrer um gol, "
    "e como isso evoluiu entre as edicoes?"
)


def competition_year(name: str) -> int:
    match = re.search(r"(\d{4})", str(name))
    return int(match.group(1)) if match else -1


summary = session.sql(
    """
    SELECT COMPETITION_NAME, CONCEDED_EVENTS, REACTED_EVENTS, PCT_REACTED,
           AVG_GOALS_AFTER_CONCEDING, PCT_ENDED_WIN,
           EVENTS_ENDED_WIN, EVENTS_ENDED_DRAW, EVENTS_ENDED_LOSS
    FROM GOLD.DIM_COMPETITION_SUMMARY
    """
).to_pandas()

if len(summary) == 0:
    st.warning("Gold vazia. Rode o pipeline / dbt run.")
    st.stop()

summary = summary.copy()
summary["YEAR"] = summary["COMPETITION_NAME"].map(competition_year)
summary = summary.sort_values(["YEAR", "COMPETITION_NAME"])

# Recorte principal do insight Databricks: finais de Copa ate 2022
plot_df = summary[
    (~summary["COMPETITION_NAME"].str.contains("Qualifying", case=False, na=False))
    & (summary["YEAR"] >= 1930)
    & (summary["YEAR"] <= 2022)
].copy()

modern = plot_df[plot_df["YEAR"].isin([2014, 2018, 2022])]
old_ref = plot_df[plot_df["YEAR"] == 1934]
sparse = plot_df[plot_df["YEAR"].isin([1990, 2006])]

m1, m2, m3, m4 = st.columns(4)
if len(modern):
    m1.metric("% reagiu (2014-2022)", f"{modern['PCT_REACTED'].mean():.1f}%")
    m2.metric("% venceu (2014-2022)", f"{modern['PCT_ENDED_WIN'].mean():.1f}%")
    m3.metric("Reacoes 2014/2018/2022", f"{int(modern['REACTED_EVENTS'].sum())}")
else:
    m1.metric("% reagiu (2014-2022)", "-")
    m2.metric("% venceu (2014-2022)", "-")
    m3.metric("Reacoes 2014/2018/2022", "-")

if len(old_ref):
    m4.metric("% reagiu (1934)", f"{float(old_ref.iloc[0]['PCT_REACTED'])}%")
else:
    m4.metric("% reagiu (1934)", "-")

st.divider()

st.subheader("Evolucao por edicao: % reagiu vs % venceu o jogo")
st.caption(
    "Mesma ideia do dashboard Databricks (barras agrupadas): "
    "reacao apos sofrer gol versus resultado final WIN do time que sofreu."
)

if len(plot_df):
    chart_evo = plot_df.set_index("YEAR")[["PCT_REACTED", "PCT_ENDED_WIN"]].rename(
        columns={
            "PCT_REACTED": "% Reagiu (fez gol depois)",
            "PCT_ENDED_WIN": "% Venceu o jogo",
        }
    )
    st.bar_chart(chart_evo, height=380)
    st.dataframe(
        plot_df[
            [
                "COMPETITION_NAME",
                "CONCEDED_EVENTS",
                "REACTED_EVENTS",
                "PCT_REACTED",
                "PCT_ENDED_WIN",
                "AVG_GOALS_AFTER_CONCEDING",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Sem edicoes finais ate 2022 para o grafico principal.")

st.subheader("Insights (alinhados ao Databricks)")
bullets = []
if len(old_ref) and len(modern):
    bullets.append(
        f"- Copas antigas (1934): reacao **{float(old_ref.iloc[0]['PCT_REACTED'])}%** / "
        f"vitoria **{float(old_ref.iloc[0]['PCT_ENDED_WIN'])}%**. "
        f"Modernas (2014-2022): reacao **~{modern['PCT_REACTED'].mean():.1f}%** / "
        f"vitoria **~{modern['PCT_ENDED_WIN'].mean():.1f}%**."
    )
if len(modern) == 3 and set(modern["REACTED_EVENTS"].astype(int).tolist()) == {75}:
    bullets.append(
        "- Em 2014, 2018 e 2022 o numero de reacoes foi **exatamente 75** em cada edicao "
        "(taxa estavel perto de 44%)."
    )
elif len(modern):
    detail_react = ", ".join(
        f"{int(r.YEAR)}={int(r.REACTED_EVENTS)}" for r in modern.itertuples()
    )
    bullets.append(f"- Reacoes por edicao moderna: {detail_react}.")
if len(sparse):
    vols = ", ".join(
        f"{int(r.YEAR)}={int(r.CONCEDED_EVENTS)} eventos" for r in sparse.itertuples()
    )
    bullets.append(
        f"- Volume baixo em {vols}: efeito tipico da quarentena quando a fonte "
        "traz minutos incompletos (mesmo sinal de DQ do Databricks)."
    )
bullets.append(
    "- A analise usa a populacao de eventos validos da fonte aberta (estudo academico), "
    "nao uma amostra amostral classica."
)
st.markdown("\n".join(bullets))

st.divider()

st.subheader("Detalhe operacional (fato / faixas)")

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
        ROUND(100.0 * AVG(REACTED_FLAG), 1) AS PCT_REAGIU
    FROM GOLD.FACT_REACTION_EVENTS
    WHERE COMPETITION_NAME IN ('World Cup 2014', 'World Cup 2018', 'World Cup 2022')
    GROUP BY 1
    ORDER BY 1
    """
).to_pandas()

by_result = session.sql(
    """
    SELECT FINAL_RESULT AS RESULTADO, COUNT(*) AS EVENTOS
    FROM GOLD.FACT_REACTION_EVENTS
    WHERE COMPETITION_NAME IN ('World Cup 2014', 'World Cup 2018', 'World Cup 2022')
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

detail = session.sql(
    """
    SELECT MATCH_DATE, COMPETITION_NAME, CONCEDING_TEAM, SCORING_TEAM, SCORER, GOAL_MINUTE,
           SCORE_DIFF_BEFORE_GOAL, GOALS_SCORED_AFTER_CONCEDING,
           FINAL_RESULT, REACTED_FLAG, IS_OWN_GOAL
    FROM GOLD.FACT_REACTION_EVENTS
    WHERE COMPETITION_NAME = 'World Cup 2022'
    ORDER BY MATCH_DATE, GOAL_MINUTE
    LIMIT 40
    """
).to_pandas()

g1, g2 = st.columns(2, gap="large")
with g1:
    st.markdown("**% de reacao por faixa de minuto (2014-2022)**")
    if len(by_minute):
        st.line_chart(by_minute.set_index("FAIXA_MINUTO")[["PCT_REAGIU"]], height=280)
with g2:
    st.markdown("**Resultado final do time que sofreu (2014-2022)**")
    if len(by_result):
        st.bar_chart(by_result.set_index("RESULTADO")[["EVENTOS"]], height=280)

with st.expander("Todas as competicoes na Gold (inclui 2026 / Qualifying)"):
    st.dataframe(
        summary.drop(columns=["YEAR"]),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Amostra de eventos - World Cup 2022"):
    st.dataframe(detail, use_container_width=True, hide_index=True)

checks = session.sql(
    """
    SELECT CHECKED_AT, CHECK_NAME, LAYER, STATUS, FAILED_ROWS, DETAILS
    FROM QC.CHECK_RESULTS
    ORDER BY CHECKED_AT DESC
    LIMIT 20
    """
).to_pandas()
with st.expander("Quality checks recentes"):
    st.dataframe(checks, use_container_width=True, hide_index=True)
