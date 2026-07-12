# Projeto Integrado: Eficiência Emocional no Futebol

Este projeto é parte do Trabalho Final do MBA em Engenharia de Dados. O pipeline processa dados históricos de torneios internacionais de futebol (Copa do Mundo e Eurocopa) utilizando a Arquitetura Medalhão para analisar e responder a hipóteses de eficiência emocional dos times.

## Pergunta de Negócio

Qual é o impacto real no desempenho e postura tática dos times logo após sofrerem um gol? 

A análise busca identificar:
- Quanto tempo um time leva para empatar ou virar uma partida após sofrer um gol.
- Se sofrer um gol aumenta a vulnerabilidade da equipe de sofrer um segundo gol em sequência.
- Possíveis diferenças no tempo de reação dependendo do torneio.

## Arquitetura e Tecnologias

O projeto foi construído focado em uma implantação automatizada na nuvem, utilizando Databricks e Unity Catalog.

- Fonte de Dados: Open Football Data (JSON)
- Processamento: Apache Spark (PySpark)
- Armazenamento: Delta Lake
- Infraestrutura como Código (IaC): Terraform

## Como Executar

### 1. Provisionamento
O ambiente do Databricks e os catálogos devem ser provisionados utilizando Terraform:
```bash
cd terraform
terraform init
terraform apply
```

### 2. Sincronização
Utilize a funcionalidade Databricks Repos no seu Workspace para conectar com este repositório do GitHub e importar os notebooks.

### 3. Execução do Pipeline
Com o repositório sincronizado no Databricks, certifique-se de que a variável de ambiente no início do notebook (ou nas configurações do cluster) está apontando para o ambiente de nuvem:
```python
ENVIRONMENT = "databricks"
```
Execute os notebooks em ordem sequencial (`01_Pipeline...`, `02_Pipeline...`). O pipeline fará a ingestão diretamente da fonte oficial e armazenará os dados estruturados de forma segura no Unity Catalog.

## Estrutura

- `01_Pipeline_Football.ipynb`: Ingestão de dados e consolidação (Camada Bronze).
- `FOUNDATION.md`: Documentação conceitual.
- `HOMEWORK.md`: Requisitos originais do projeto.
- `terraform/`: Código IaC para criação da infraestrutura.
