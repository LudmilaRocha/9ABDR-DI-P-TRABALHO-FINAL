# Comparação: Databricks vs. Snowflake

**Responsável:** Guilherme Csorgo  
**Deadline:** 24/07/2025  
**Base:** pipelines descritos em [ARCHITECTURE.md](ARCHITECTURE.md), implementados em [databricks/](databricks/) e [snowflake/](snowflake/), sobre a mesma fonte (`openfootball/worldcup.json`) e a mesma regra de negócio.

## 1. Facilidade de uso

| Critério | Databricks | Snowflake |
|---|---|---|
| Linguagem principal | PySpark (notebooks `.ipynb`) | SQL puro + Python auxiliar (`run_snowflake_sql.py`) |
| Curva de aprendizado | Exige conhecimento de Spark (DataFrames, joins, window functions, etc) | Exige só SQL (self-join, CTEs). Mais acessível para quem já sabe SQL |
| Interface de desenvolvimento | Notebook interativo (célula a célula, com prints/gráficos inline) | Scripts `.sql` numerados executados via CLI (`run_snowflake_sql.py`) ou Snowsight |
| Orquestração das camadas | Execução sequencial dos 4 notebooks | Procedures encadeadas + Tasks (`06_pipeline_procedures_and_schedule.sql`) |
| Time to market** | 2 semanas (business hours) | **PENDENTE** |

> ** O tempo de desenvolvimento não leva em consideração a expertise de cada usuário nas plataformas

### Evidências
**PENDENTE (Membro 2 e Membro 3):** print de tela do Databricks Workspace e do Snowsight mostrando a execução de ponta a ponta, para ilustrar a diferença de experiência.

---

## 2. Ingestão / transformação

| Critério | Databricks | Snowflake |
|---|---|---|
| Ingestão Bronze | PySpark lê JSON direto, grava em Delta (`MERGE` incremental) | Python baixa/achata em CSV local, `COPY INTO` via stage interno |
| Formato de armazenamento | Delta Lake (ACID, time travel nativo) | Tabelas nativas Snowflake (ACID nativo, sem versionamento de arquivo explícito no pipeline) |
| Camada Silver | PySpark: tipagem, quarentena por regras de qualidade | SQL: tipagem (`TRY_TO_...`), quarentena pelas mesmas regras (minuto 0–130, placar não negativo) |
| Camada Gold | PySpark + SQL, self-join temporal para `reacted_flag` | SQL puro, mesma lógica de self-join (dbt models idênticos aos do Databricks) |
| Evolução de schema | Unity Catalog | Schema Evolution nativo do Snowflake |

**Observação:** a lógica de negócio da camada Gold é **literalmente igual** nos dois projetos dbt (`databricks/dbt_openfootball/` e `snowflake/dbt_openfootball/`), então a diferença aqui é puramente de engine/sintaxe, não de resultado.

**PENDENTE (Membro 2 e Membro 3):** volume de dados processado (linhas em Bronze/Silver/Gold) e tempo de execução de cada camada, para comparar throughput.

---

## 3. Performance

| Critério | Databricks | Snowflake |
|---|---|---|
| Modelo de computação | Cluster Spark (paralelismo distribuído) | Warehouse `WH_DI_P_PIPELINE`, tamanho `XSMALL`, auto-suspend em 60s |
| Adequação ao volume do projeto | "Overkill" para o volume atual (dezenas de milhares de partidas). Spark compensa em volumes muito maiores | Adequado ao volume atual; warehouse pequeno já suficiente |
| Tempo de execução Medalion | **PENDENTE** | **PENDENTE** |
| Custo de "cold start" | Cluster leva minutos para subir (se não estiver always-on) | Warehouse XSMALL sobe em segundos |

**PENDENTE (Membro 2 e Membro 3):** tempos reais de execução (prints do histórico de jobs/queries) e tamanho do cluster/warehouse usado em cada teste.

---

## 4. Governança

| Critério | Databricks | Snowflake |
|---|---|---|
| Catálogo/organização | Unity Catalog (`workspace.bronze/silver/gold`) | Banco `DI_P_MEDALLION` com schemas `BRONZE/SILVER/GOLD/QC/PIPE` |
| Linhagem (lineage) | Unity Catalog rastreia automaticamente | Rastreada manualmente via `SOURCE_FILE`, `_RUN_ID`, `QC.PIPELINE_RUNS` |
| Controle de acesso | Unity Catalog RBAC | RBAC nativo do Snowflake (roles/grants). Não implementado explicitamente nos scripts do trabalho |
| Qualidade de dados | Quarentena em tabelas Delta separadas | Quarentena em tabelas + `QC.CHECK_RESULTS`/`QC.PIPELINE_RUNS` + testes dbt |
| Dados sensíveis | N/A (base pública, sem PII) | N/A (base pública, sem PII) |

**PENDENTE:** confirmar com o Membro 5 se há algo específico de governança já decidido que deva entrar nesta tabela.

---

## 5. Custo

### Modelo de cobrança

**Databricks: DBU (Databricks Unit):**
- Cobrança por DBU consumida × preço por DBU (varia por tier: Standard, Premium, Enterprise) + custo de infraestrutura cloud subjacente (VM do cluster).
- Ordem de grandeza de referência (verificar tabela vigente do provedor antes de fechar o número): **PENDENTE**.

**Snowflake: crédito de warehouse + storage:**
- Cobrança por **crédito** consumido pelo warehouse (1 crédito/hora para `XSMALL`, dobra a cada tamanho) + armazenamento (~US$/TB/mês, cobrado separado do compute).
- Warehouse do projeto: `XSMALL`, `AUTO_SUSPEND = 60` (economiza créditos entre execuções, já que o pipeline roda 1x/semana).

### Estimativa para o cenário do grupo


| Item | Databricks | Snowflake |
|---|---|---|
| Frequência de execução | Semanal (± diária em mês de Copa) | Semanal (± diária em mês de Copa) |
| Tempo estimado por execução | PENDENTE | PENDENTE |
| Custo estimado por execução | PENDENTE | PENDENTE |
| Custo estimado mensal (fora de Copa) | PENDENTE | PENDENTE |
| Custo estimado mensal (mês de Copa) | PENDENTE | PENDENTE |

**PENDENTE (Membro 2 e Membro 3):** cole aqui o print da fatura/estimativa de custo (Databricks: aba de billing/DBU; Snowflake: `ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY` ou Snowsight > Cost Management) referente às execuções reais do pipeline.

> Consultar `ARCHITECTURE.md` para detalhes da frequencia de execução.

---

## 6. Conclusão

**PENDENTE**: Escrever após preencher as seções de performance e custo acima.**

Rascunho (a confirmar/ajustar com os números reais):
- Para o **volume atual do projeto** (dezenas de milhares de partidas, atualização semanal), Snowflake tende a ter custo/operação mais simples: warehouse pequeno, sem necessidade de gerenciar cluster Spark, SQL puro reduz a barreira de manutenção.
- Databricks se justificaria melhor se o volume crescesse por ordens de grandeza (ex.: ingestão de eventos em tempo real, múltiplas fontes de dados não estruturados) ou se o time já tivesse forte expertise em Spark/ML no mesmo workspace.
- A decisão final deve pesar não só custo/performance no volume atual, mas também para onde o grupo imagina esse pipeline crescer.
