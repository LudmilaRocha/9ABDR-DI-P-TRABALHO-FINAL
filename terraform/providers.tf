terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0.0"
    }
  }
}

# Configuração do Provedor do Databricks
# As credenciais (URL do Workspace e Token) devem ser passadas via variáveis de ambiente
# DATABRICKS_HOST e DATABRICKS_TOKEN ou configuradas usando o Databricks CLI.
provider "databricks" {}
