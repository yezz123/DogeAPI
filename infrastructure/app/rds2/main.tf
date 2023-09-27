terraform {
  required_version = "~> 1.5.6"

  backend "s3" {
    bucket   = "cafi-demo1"
    key      = "demos/dogeapi/rds2/terraform.tfstate"
    region   = "us-east-1"
    role_arn = "arn:aws:iam::180217099948:role/atlantis-access"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  assume_role {
    role_arn = "arn:aws:iam::180217099948:role/atlantis-access"
  }
}

locals {
  tags = {
    Terraform   = "True"
    Environment = var.environment
  }
}

# PostgreSQL Serverless v2
data "aws_rds_engine_version" "postgresql" {
  engine  = "aurora-postgresql"
  version = var.postgresql_engine_version
}


resource "aws_rds_cluster" "this" {
  cluster_identifier      = "${var.database_name}-${var.environment}"
  engine                  = data.aws_rds_engine_version.postgresql.engine
  engine_version          = data.aws_rds_engine_version.postgresql.version
  engine_mode             = "provisioned"
  database_name           = var.database_name
  master_username         = "root"
  master_password         = var.master_password
  backup_retention_period = var.backup_retention_period
  skip_final_snapshot     = true
  storage_encrypted       = true

  serverlessv2_scaling_configuration {
    max_capacity = 10
    min_capacity = 0.5
  }

  tags = local.tags
}
