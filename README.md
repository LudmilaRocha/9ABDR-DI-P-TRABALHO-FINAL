# Projeto Integrado: Eficiência Emocional no Futebol

Este projeto é parte do Trabalho Final do MBA em Engenharia de Dados. O pipeline processa dados históricos de torneios internacionais de futebol (Copa do Mundo e Eurocopa) utilizando a Arquitetura Medalhão para analisar e responder a hipóteses de eficiência emocional dos times.

## Pergunta de Negócio

Qual é o impacto real no desempenho e postura tática dos times logo após sofrerem um gol? 

A análise busca identificar:
- Quanto tempo um time leva para empatar ou virar uma partida após sofrer um gol.
- Se sofrer um gol aumenta a vulnerabilidade da equipe de sofrer um segundo gol em sequência.
- Possíveis diferenças no tempo de reação dependendo do torneio.

## Arquitetura e Tecnologias

O projeto foi construído seguindo as melhores práticas de **Agnosticismo de Plataforma (Multi-Cloud)**, permitindo execução tanto em nuvem corporativa (Databricks) quanto em ambientes locais (Docker).

- Fonte de Dados: Open Football Data (JSON)
- Processamento: Apache Spark (PySpark)
- Armazenamento: Delta Lake (Unity Catalog na nuvem ou pasta local)

## Como Executar (Databricks Cloud)

### 1. Sincronização (Repos)
Utilize a funcionalidade **Databricks Repos** no seu Workspace para conectar com este repositório do GitHub e importar os notebooks de forma versionada.

### 2. Execução do Pipeline Automático
Abra o notebook da primeira camada e certifique-se de que a variável de ambiente no início do código (ou nas configurações do cluster) está apontando para o ambiente de nuvem:
```python
ENVIRONMENT = "databricks"
```
Em seguida, clique em **"Run All"** no notebook `01_Pipeline_Football.ipynb`. Ele fará automaticamente:
1. O download seguro dos arquivos brutos (JSON) das fontes oficiais.
2. A criação dinâmica e validação dos *Schemas* (bancos Bronze, Silver e Gold) utilizando Databricks SQL puro (dispensando permissões externas de APIs).
3. A ingestão, limpeza inicial e persistência dos dados na tabela Delta `workspace.bronze.matches`.

*(As Camadas Silver e Gold seguem a mesma lógica e fluxo de execução nos notebooks sequenciais).*

## Estrutura do Repositório

- `01_Pipeline_Football.ipynb`: Ingestão, modelagem e consolidação (Camada Bronze).
- `FOUNDATION.md`: Documentação arquitetural conceitual.
- `HOMEWORK.md`: Requisitos e diretrizes originais do Trabalho Final.
