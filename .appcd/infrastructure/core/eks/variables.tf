variable "environment" {
  description = "Environment name"
}

variable "aws_region" {
  description = "AWS region"
}

variable "cluster_name" {
  description = "Cluster name"
  default     = "demo"
}

variable "cluster_version" {
  default = "1.24"
}

variable "vpc_id" {
  description = "VPC ID"
}

variable "azs" {
  description = "Availability zones"
  type        = list(string)
}

variable "private_subnets" {
  description = "Private subnets"
  type        = list(string)
}
