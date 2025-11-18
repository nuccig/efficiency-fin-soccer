output "s3_bucket_name" {
  description = "Nome do bucket S3"
  value       = aws_s3_bucket.data_lake.id
}

output "s3_bucket_arn" {
  description = "ARN do bucket S3"
  value       = aws_s3_bucket.data_lake.arn
}

output "rds_endpoint" {
  description = "Endpoint do RDS PostgreSQL"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "Endereço do RDS PostgreSQL"
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "Porta do RDS PostgreSQL"
  value       = aws_db_instance.postgres.port
}

output "rds_database_name" {
  description = "Nome do database PostgreSQL"
  value       = aws_db_instance.postgres.db_name
}

output "vpc_id" {
  description = "ID da VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "IDs das subnets privadas"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "IDs das subnets públicas"
  value       = aws_subnet.public[*].id
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

output "glue_financial_crawler_name" {
  description = "Nome do crawler Glue para dados financeiros"
  value       = aws_glue_crawler.financial_data.name
}

# Athena Outputs
output "athena_workgroup_name" {
  description = "Nome do workgroup do Athena"
  value       = aws_athena_workgroup.main.name
}

output "athena_results_bucket" {
  description = "Bucket S3 para resultados de queries do Athena"
  value       = aws_s3_bucket.athena_results.bucket
}
