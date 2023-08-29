variable "environment" {
  description = "Environment name"
}

variable "aws_region" {
  description = "AWS region"
}

variable "state_bucket_name" {
  description = "State bucket name"
  default     = "cafi-demo1"
}

variable "state_bucket_vpc_key" {
  description = "State bucket VPC key"
  default     = "demos/core/vpc/terraform.tfstate"
}

variable "state_bucket_region" {
  description = "State bucket region"
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Cluster name"
  default     = "demo"
}

variable "cluster_version" {
  default = "1.24"
}
