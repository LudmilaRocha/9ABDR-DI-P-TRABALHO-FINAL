# 1. Referência ao Catálogo (Assumindo que o catálogo "workspace" já existe no Databricks)
data "databricks_catalog" "workspace" {
  name = var.catalog_name
}

# 2. Arquitetura Medalhão: Criação dos Schemas (Databases)
resource "databricks_schema" "bronze" {
  catalog_name = data.databricks_catalog.workspace.name
  name         = var.schema_bronze_name
  comment      = "Camada Bronze: Dados brutos recém injetados"
}

resource "databricks_schema" "silver" {
  catalog_name = data.databricks_catalog.workspace.name
  name         = var.schema_silver_name
  comment      = "Camada Silver: Dados limpos, filtrados e enriquecidos"
}

resource "databricks_schema" "gold" {
  catalog_name = data.databricks_catalog.workspace.name
  name         = var.schema_gold_name
  comment      = "Camada Gold: Agregações focadas na regra de negócio (Eficiência Emocional)"
}

# 3. Criação do Volume para arquivos brutos dentro do Schema Bronze
resource "databricks_volume" "football_raw" {
  name         = var.volume_name
  catalog_name = data.databricks_catalog.workspace.name
  schema_name  = databricks_schema.bronze.name
  volume_type  = "MANAGED"
  comment      = "Volume gerenciado para ingestão dos zips/jsons/txts do Open Football"
}
