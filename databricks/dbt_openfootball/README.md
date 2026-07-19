# dbt for Databricks (Agnosticismo de Regras de Negócio)

Este diretório contém a réplica exata das regras de negócio (Camadas Silver e Gold) escritas originalmente para o Snowflake, agora adaptadas para o **Databricks SQL**.

## Objetivo

O propósito deste diretório é provar o conceito de **Regras de Negócio Agnósticas à Plataforma**. 

A arquitetura original deste projeto no Databricks utiliza **PySpark** para demonstrar flexibilidade de infraestrutura (podendo rodar localmente ou na nuvem). No entanto, caso a diretriz arquitetural da empresa exija que *todas* as transformações sejam feitas em SQL (ELT clássico), este projeto dbt pode ser acoplado ao Databricks SQL Warehouse.

Com isso, o Databricks executará os arquivos `.sql` e gerará os exatos mesmos resultados nas tabelas `fact_reaction_events` e `dim_competition_summary` usando a engine do Databricks SQL, em vez do PySpark.

## Estrutura

- `models/silver/goal_events.sql`: Lógica de limpeza adaptada com `TRY_CAST` suportado pelo Databricks SQL.
- `models/gold/fact_reaction_events.sql`: Tabela Fato usando ANSI SQL e window functions (via subqueries e self-joins) compatíveis.
- `models/gold/dim_competition_summary.sql`: Tabela Dimensão/Métricas.

## Como Executar

Se você tiver um Databricks SQL Warehouse configurado e o `dbt-databricks` instalado:

```bash
dbt run --profiles-dir .
```
