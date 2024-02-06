variable "environment" {
  description = "Environment name"
}

variable "aws_region" {
  description = "AWS region"
}

variable "database_name" {
  description = "Database name"
}

variable "postgresql_engine_version" {
  description = "PostgreSQL engine version"
  default     = "15.2"
}

variable "db_subnet_group_name" {
  description = "Database subnet group name"
}

variable "private_subnets_cidr_blocks" {
  description = "Private subnets CIDR blocks"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC ID"
}
