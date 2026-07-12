# Infraestrutura como Código (IaC) - Pipeline de Futebol

Este diretório contém os scripts do **Terraform** para provisionamento automatizado da infraestrutura de dados.

Em um ambiente de produção moderno de Engenharia de Dados, o notebook (código de ETL) não deve ser responsável por criar os bancos de dados ou a estrutura de armazenamento. Ele deve focar em manipular os dados. A infraestrutura base deve ser criada via IaC (Infraestructure as Code).

## Provider Oficial: Databricks
Na raiz desta pasta, os arquivos (`main.tf`, `variables.tf`, `providers.tf`) configuram a Arquitetura Medalhão no Databricks Unity Catalog.
- O schema (database): `workspace.bronze`, `workspace.silver`, `workspace.gold`
- O volume gerenciado para os arquivos raw: `workspace.bronze.football_raw`

## Exemplos Multicloud (Agnosticismo)
Para demonstrar que a arquitetura do projeto (Medalhão) é um conceito agnóstico, a pasta `/multicloud_examples` contém esqueletos de como essa mesma infraestrutura seria provisionada de forma nativa nos Três Grandes Provedores de Nuvem (AWS, Azure e Google Cloud), sem usar o Databricks.

Estes arquivos possuem a extensão `.tf.example` para que o Terraform os ignore durante uma execução real (`terraform apply`), servindo apenas como documentação arquitetural.

## Como utilizar (Conceitual)
1. **Instalação:** Você instala a CLI (linha de comando) do Terraform e do Databricks na sua máquina local ou em uma esteira de CI/CD (ex: GitHub Actions).
2. **Autenticação:** O Terraform usa o Databricks CLI ou um Token para se conectar ao seu workspace de forma segura (sem colocar senhas no código).
3. **Comandos principais:**
   - `terraform init` (Prepara e baixa os conectores)
   - `terraform plan` (Mostra o que ele vai criar, sem aplicar ainda)
   - `terraform apply` (Conecta na nuvem e efetivamente cria a infraestrutura)
