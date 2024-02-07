terraform {
  required_version = "~> 1.5.6"

  backend "s3" {
    bucket   = "cafi-demo1"
    key      = "demos/dogeapi/rds/terraform.tfstate"
    region   = "us-east-1"
    role_arn = "arn:aws:iam::180217099948:role/atlantis-access"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
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

module "aurora_postgresql_v2" {
  source = "terraform-aws-modules/rds-aurora/aws"

  name                        = "${var.database_name}-${var.environment}"
  engine                      = data.aws_rds_engine_version.postgresql.engine
  engine_mode                 = "provisioned"
  engine_version              = data.aws_rds_engine_version.postgresql.version
  storage_encrypted           = true
  manage_master_user_password = true
  master_username             = "root"

  vpc_id               = var.vpc_id
  db_subnet_group_name = var.db_subnet_group_name
  security_group_rules = {
    vpc_ingress = {
      cidr_blocks = var.private_subnets_cidr_blocks
    }
  }

  # Enhanced monitoring disabled for now
  monitoring_interval = 0

  apply_immediately   = true
  skip_final_snapshot = true

  serverlessv2_scaling_configuration = {
    min_capacity = 0.5
    max_capacity = 1
  }

  instance_class = "db.serverless"
  instances = {
    one = {}
    two = {}
  }

  tags = local.tags
}
