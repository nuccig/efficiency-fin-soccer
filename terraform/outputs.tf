output "s3_bucket_name" {
  description = "Nome do bucket S3"
  value       = aws_s3_bucket.data_lake.id
}

output "s3_bucket_arn" {
  description = "ARN do bucket S3"
  value       = aws_s3_bucket.data_lake.arn
}

# RDS Outputs (Opcional - apenas se enable_rds = true)
output "rds_endpoint" {
  description = "Endpoint do RDS PostgreSQL"
  value       = var.enable_rds ? aws_db_instance.postgres[0].endpoint : null
}

output "rds_address" {
  description = "Endereço do RDS PostgreSQL"
  value       = var.enable_rds ? aws_db_instance.postgres[0].address : null
}

output "rds_port" {
  description = "Porta do RDS PostgreSQL"
  value       = var.enable_rds ? aws_db_instance.postgres[0].port : null
}

output "rds_database_name" {
  description = "Nome do database PostgreSQL"
  value       = var.enable_rds ? aws_db_instance.postgres[0].db_name : null
}

# Network Outputs (Opcional - apenas se enable_vpc = true)
output "vpc_id" {
  description = "ID da VPC"
  value       = var.enable_vpc ? aws_vpc.main[0].id : null
}

output "private_subnet_ids" {
  description = "IDs das subnets privadas"
  value       = var.enable_vpc ? aws_subnet.private[*].id : []
}

output "public_subnet_ids" {
  description = "IDs das subnets públicas"
  value       = var.enable_vpc ? aws_subnet.public[*].id : []
}

# Glue Outputs
output "glue_database_name" {
  description = "Nome do database do Glue Data Catalog"
  value       = aws_glue_catalog_database.data_catalog.name
}

output "glue_sport_crawler_name" {
  description = "Nome do crawler Glue para dados esportivos"
  value       = aws_glue_crawler.sport_data.name
}

# Crawler financeiro foi substituído por tabelas manuais
# output "glue_financial_crawler_name" {
#   description = "Nome do crawler Glue para dados financeiros"
#   value       = aws_glue_crawler.financial_data.name
# }

# Athena Outputs
output "athena_workgroup_name" {
  description = "Nome do workgroup do Athena"
  value       = aws_athena_workgroup.main.name
}

output "athena_results_bucket" {
  description = "Bucket S3 para resultados de queries do Athena"
  value       = aws_s3_bucket.athena_results.bucket
}
