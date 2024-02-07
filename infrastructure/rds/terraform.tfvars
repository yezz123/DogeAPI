environment               = "demo"
aws_region                = "us-east-2"
database_name             = "dogeapi-db"
postgresql_engine_version = "15.2"
db_subnet_group_name      = "demo-vpc-demo"
private_subnets_cidr_blocks = [
  "10.0.3.0/24",
  "10.0.4.0/24",
  "10.0.5.0/24",
]
vpc_id = "vpc-0c37ffe0affae162f"
