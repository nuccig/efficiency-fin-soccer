variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "efficiency-fin-soccer"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

# RDS Configuration (Opcional - não necessário para analytics)
variable "enable_rds" {
  description = "Habilitar criação de RDS PostgreSQL (não necessário para analytics)"
  type        = bool
  default     = false
}

variable "db_name" {
  description = "RDS database name"
  type        = string
  default     = "soccer_db"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 10
}

# Network Configuration (Opcional - não necessário para S3/Glue/Athena)
variable "enable_vpc" {
  description = "Habilitar criação de VPC (necessário apenas se usar RDS)"
  type        = bool
  default     = false
}
