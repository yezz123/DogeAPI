terraform {
  required_version = ">= 0.13.1"
  backend "s3" {
    bucket         = "cafi-dev-state-bucket"
    key            = "cafi-dev/demos/core/vpc/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "cafi-dev-terraform-state-lock"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.9"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {}

locals {
  vpc_name = "${var.vpc_name}-${var.environment}"
  azs      = slice(data.aws_availability_zones.available.names, 0, 3)

  tags = {
    Name        = local.vpc_name
    Terraform   = "True"
    Environment = var.environment
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 4.0"

  name = local.vpc_name
  cidr = var.vpc_cidr

  azs              = local.azs
  public_subnets   = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 8, k)]
  private_subnets  = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 8, k + 3)]
  database_subnets = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 8, k + 6)]

  enable_nat_gateway = true
  single_nat_gateway = true
  one_nat_gateway_per_az = false

  tags = local.tags
}
