# RDS Resources (Opcional - habilitar apenas se necessário)
# Para analytics, S3 + Athena é suficiente, RDS não é necessário

resource "aws_db_subnet_group" "postgres" {
  count      = var.enable_rds && var.enable_vpc ? 1 : 0
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = aws_subnet.public[*].id

  tags = {
    Name        = "${var.project_name}-db-subnet-group"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_security_group" "rds" {
  count       = var.enable_rds && var.enable_vpc ? 1 : 0
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.main[0].id

  ingress {
    description = "PostgreSQL from anywhere"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-rds-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_db_instance" "postgres" {
  count                  = var.enable_rds ? 1 : 0
  identifier             = "${var.project_name}-${var.environment}-db"
  engine                 = "postgres"
  engine_version         = "17.2"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  storage_type           = "gp3"
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = var.enable_vpc ? aws_db_subnet_group.postgres[0].name : null
  vpc_security_group_ids = var.enable_vpc ? [aws_security_group.rds[0].id] : []

  skip_final_snapshot        = true
  publicly_accessible        = true
  multi_az                   = false
  backup_retention_period    = 0
  auto_minor_version_upgrade = false
  deletion_protection        = false

  tags = {
    Name        = "${var.project_name}-postgres"
    Environment = var.environment
    Project     = var.project_name
  }
}
