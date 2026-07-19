# World Cup Analytics — Capacidade de Reação das Seleções

Projeto Final do MBA em Engenharia de Dados. Pipeline de Big Data com Arquitetura Medallion (Bronze → Silver → Gold) para análise histórica de Copas do Mundo FIFA (1930–2026).

---

## Pergunta de Negócio

> Qual percentual das seleções reage após sofrer um gol, e como essa taxa evoluiu ao longo das edições da Copa do Mundo?

**Por que Copa do Mundo e não ligas nacionais?**
- Torneio eliminatório com pressão psicológica máxima, ideal para medir resiliência.
- Nivelamento técnico entre seleções, sem as disparidades financeiras de ligas domésticas.
- Dados disponíveis desde 1930, permitindo análise de evolução tática ao longo de quase um século.

---

## Fonte de Dados

Repositório open-source **openfootball/worldcup.json** (GitHub) — base de dados aberta com registros históricos de partidas e eventos de gol das Copas do Mundo (jogador, minuto, tipo de gol, sequência temporal).

---

## Arquitetura do Pipeline

O pipeline foi construído com **PySpark** e **Delta Lake**, de forma agnóstica: o mesmo código roda em Databricks (nuvem) ou em ambiente local (Docker/Jupyter), controlado por uma única variável de ambiente (`ENVIRONMENT`).

```
                        ARQUITETURA MEDALLION
  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │   [openfootball/worldcup.json]                                  │
  │        │                                                        │
  │        ▼                                                        │
  │   ┌──────────┐    ┌──────────┐    ┌──────────────────────────┐  │
  │   │  BRONZE  │───▶│  SILVER  │───▶│          GOLD            │  │
  │   │  (Raw)   │    │(Cleansed)│    │  (Business / Serving)    │  │
  │   └──────────┘    └──────────┘    └──────────────────────────┘  │
  │    matches         matches         fact_reaction_events (Fato)  │
  │    events          goal_events     dim_competition_summary      │
  │                    quarantine_*       (Dimensão / Data Mart)    │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
```

### Camada Bronze (Raw)
Ingestão dos JSONs brutos da API sem nenhuma transformação. Registro histórico imutável. Schema flexível para absorver mudanças de tipagem na fonte original (Schema Evolution).

### Camada Silver (Cleansed)

- Tipagem das colunas e conversão segura de formatos (ex: conversão de acréscimos "90+10" para minutos inteiros).
- Padronização e renomeação de campos
- Regras de Data Quality: registros inválidos (minuto nulo, fora do intervalo 0–130) são desviados para **tabelas de quarentena**, preservando a integridade analítica

### Camada Gold (Business / Star Schema)
Modelagem dimensional voltada para consumo de BI:

| Tabela | Tipo | Granularidade | Descrição |
|--------|------|---------------|-----------|
| `fact_reaction_events` | Fato Analítica | Evento (gol a gol) | Flag binária (0/1) indicando se o time que sofreu o gol reagiu marcando nos minutos seguintes |
| `dim_competition_summary` | Dimensão / Data Mart | Competição (Copa) | KPIs agregados por edição: % de reação, % de virada, média de gols pós-gol sofrido |

> **Nota:** A nomenclatura `fact_` e `dim_` é aplicada exclusivamente na Camada Gold, onde os dados são modelados para consumo de ferramentas de BI (Star Schema). As camadas Bronze e Silver utilizam nomenclatura de entidades de negócio.

---



## Regras de Negócio

1. **Cálculo do placar parcial:** Self-Join temporal na tabela de eventos para reconstruir o placar exato no momento de cada gol (quantos gols cada time tinha *antes* daquele evento).
2. **Detecção de reação:** Contagem de gols marcados pelo time que sofreu o gol nos minutos *posteriores* ao evento. Se > 0, a flag `reacted_flag` recebe valor 1.
3. **Resultado final sob a ótica do time que sofreu:** Classificação em WIN, DRAW ou LOSS com base no placar final (full-time).
4. **Agregação por competição:** Cálculo de `pct_reacted` (% de reação) e `pct_ended_win` (% de virada) por edição da Copa.

---

## Conclusões

| Indicador | Copas Antigas (1934) | Copas Modernas (2014–2022) |
|-----------|---------------------|---------------------------|
| Taxa de Reação | ~60% | ~44% |
| Taxa de Virada (Vitória) | ~25% | ~15% |

- Nas edições de 2014, 2018 e 2022, o número de reações foi **exatamente 75** em cada uma, com taxa estável em ~44%.
- A queda volumétrica em edições como 1990 e 2006 comprova o funcionamento das regras de Data Quality, que isolaram dados incompletos da API.
- Por se tratar de processamento da **população total** de eventos (censo), a margem de erro estatística é zero.

---

## Estrutura dos Notebooks

```
databricks v2/
├── 00_Pipeline_Football_Setup.ipynb      # Configuração agnóstica de ambiente
├── 01_Pipeline_Football_Bronze.ipynb     # Ingestão bruta (API → Delta)
├── 02_Pipeline_Football_Silver.ipynb     # Limpeza, tipagem e quarentena
└── 03_Pipeline_Football_Gold.ipynb       # Regras de negócio e modelagem dimensional
```
