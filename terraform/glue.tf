# Glue Database
resource "aws_glue_catalog_database" "data_catalog" {
  name        = "${var.project_name}_${var.environment}_catalog"
  description = "Data catalog for football data lake"

  tags = {
    Name        = "${var.project_name}-data-catalog"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Role for Glue Crawler
resource "aws_iam_role" "glue_crawler" {
  name = "${var.project_name}-${var.environment}-glue-crawler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-glue-crawler-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach AWS managed Glue service policy
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_crawler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# Custom policy for S3 access
resource "aws_iam_policy" "glue_s3_access" {
  name        = "${var.project_name}-${var.environment}-glue-s3-access"
  description = "Allow Glue crawler to access S3 data lake"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-glue-s3-policy"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach S3 access policy
resource "aws_iam_role_policy_attachment" "glue_s3" {
  role       = aws_iam_role.glue_crawler.name
  policy_arn = aws_iam_policy.glue_s3_access.arn
}

# Glue Crawler for Sport Data
resource "aws_glue_crawler" "sport_data" {
  name          = "${var.project_name}-${var.environment}-sport-crawler"
  role          = aws_iam_role.glue_crawler.arn
  database_name = aws_glue_catalog_database.data_catalog.name

  description = "Crawler for football sport data (seasons and players)"

  # Crawl both seasons and players folders
  s3_target {
    path = "s3://${aws_s3_bucket.data_lake.bucket}/sport/seasons/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.data_lake.bucket}/sport/players/"
  }

  # Configuration
  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })

  # Schema change policy
  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = {
    Name        = "${var.project_name}-sport-crawler"
    Environment = var.environment
    Project     = var.project_name
  }

  depends_on = [
    aws_iam_role_policy_attachment.glue_service,
    aws_iam_role_policy_attachment.glue_s3
  ]
}

# Optional: Glue Crawler for Financial Data (if needed in future)
resource "aws_glue_crawler" "financial_data" {
  name          = "${var.project_name}-${var.environment}-financial-crawler"
  role          = aws_iam_role.glue_crawler.arn
  database_name = aws_glue_catalog_database.data_catalog.name

  description = "Crawler for financial data"

  s3_target {
    path = "s3://${aws_s3_bucket.data_lake.bucket}/financial/"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
  })

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = {
    Name        = "${var.project_name}-financial-crawler"
    Environment = var.environment
    Project     = var.project_name
  }

  depends_on = [
    aws_iam_role_policy_attachment.glue_service,
    aws_iam_role_policy_attachment.glue_s3
  ]
}
