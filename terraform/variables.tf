variable "catalog_name" {
  type        = string
  description = "Nome do Catálogo principal (ex: workspace, hive_metastore, main)"
  default     = "workspace"
}

variable "schema_bronze_name" {
  type        = string
  description = "Nome do Schema/Database para a camada Bronze"
  default     = "bronze"
}

variable "schema_silver_name" {
  type        = string
  description = "Nome do Schema/Database para a camada Silver"
  default     = "silver"
}

variable "schema_gold_name" {
  type        = string
  description = "Nome do Schema/Database para a camada Gold"
  default     = "gold"
}

variable "volume_name" {
  type        = string
  description = "Nome do Volume do Unity Catalog para guardar os arquivos raw"
  default     = "football_raw"
}
