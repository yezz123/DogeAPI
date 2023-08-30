variable "environment" {
  description = "Environment name"
}

variable "aws_region" {
  description = "AWS region"
}

variable "vpc_name" {
  description = "VPC name"
}

variable "vpc_cidr" {
  description = "VPC CIDR"
  default     = "10.0.0.0/16"
}
