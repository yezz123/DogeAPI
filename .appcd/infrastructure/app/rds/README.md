# RDS

Infrastructure templates used to manage the Postgres RDS DB cluster

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.13.1 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 4.9 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 4.65.0 |
| <a name="provider_terraform"></a> [terraform](#provider\_terraform) | n/a |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_aurora_postgresql_v2"></a> [aurora\_postgresql\_v2](#module\_aurora\_postgresql\_v2) | terraform-aws-modules/rds-aurora/aws | n/a |

## Resources

| Name | Type |
|------|------|
| [aws_rds_engine_version.postgresql](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/rds_engine_version) | data source |
| [terraform_remote_state.vpc](https://registry.terraform.io/providers/hashicorp/terraform/latest/docs/data-sources/remote_state) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | AWS region | `any` | n/a | yes |
| <a name="input_database_name"></a> [database\_name](#input\_database\_name) | Database name | `any` | n/a | yes |
| <a name="input_environment"></a> [environment](#input\_environment) | Environment name | `any` | n/a | yes |
| <a name="input_postgresql_engine_version"></a> [postgresql\_engine\_version](#input\_postgresql\_engine\_version) | PostgreSQL engine version | `string` | `"15.2"` | no |
| <a name="input_state_bucket_name"></a> [state\_bucket\_name](#input\_state\_bucket\_name) | State bucket name | `string` | `"cafi-dev-state-bucket"` | no |
| <a name="input_state_bucket_region"></a> [state\_bucket\_region](#input\_state\_bucket\_region) | State bucket region | `string` | `"us-east-1"` | no |
| <a name="input_state_bucket_vpc_key"></a> [state\_bucket\_vpc\_key](#input\_state\_bucket\_vpc\_key) | State bucket VPC key | `string` | `"cafi-dev/cafi/infrastructure/vpc/terraform.tfstate"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_aurora_postgresql_v2_additional_cluster_endpoints"></a> [aurora\_postgresql\_v2\_additional\_cluster\_endpoints](#output\_aurora\_postgresql\_v2\_additional\_cluster\_endpoints) | A map of additional cluster endpoints and their attributes |
| <a name="output_aurora_postgresql_v2_cluster_arn"></a> [aurora\_postgresql\_v2\_cluster\_arn](#output\_aurora\_postgresql\_v2\_cluster\_arn) | Amazon Resource Name (ARN) of cluster |
| <a name="output_aurora_postgresql_v2_cluster_database_name"></a> [aurora\_postgresql\_v2\_cluster\_database\_name](#output\_aurora\_postgresql\_v2\_cluster\_database\_name) | Name for an automatically created database on cluster creation |
| <a name="output_aurora_postgresql_v2_cluster_endpoint"></a> [aurora\_postgresql\_v2\_cluster\_endpoint](#output\_aurora\_postgresql\_v2\_cluster\_endpoint) | Writer endpoint for the cluster |
| <a name="output_aurora_postgresql_v2_cluster_engine_version_actual"></a> [aurora\_postgresql\_v2\_cluster\_engine\_version\_actual](#output\_aurora\_postgresql\_v2\_cluster\_engine\_version\_actual) | The running version of the cluster database |
| <a name="output_aurora_postgresql_v2_cluster_hosted_zone_id"></a> [aurora\_postgresql\_v2\_cluster\_hosted\_zone\_id](#output\_aurora\_postgresql\_v2\_cluster\_hosted\_zone\_id) | The Route53 Hosted Zone ID of the endpoint |
| <a name="output_aurora_postgresql_v2_cluster_id"></a> [aurora\_postgresql\_v2\_cluster\_id](#output\_aurora\_postgresql\_v2\_cluster\_id) | The RDS Cluster Identifier |
| <a name="output_aurora_postgresql_v2_cluster_instances"></a> [aurora\_postgresql\_v2\_cluster\_instances](#output\_aurora\_postgresql\_v2\_cluster\_instances) | A map of cluster instances and their attributes |
| <a name="output_aurora_postgresql_v2_cluster_master_password"></a> [aurora\_postgresql\_v2\_cluster\_master\_password](#output\_aurora\_postgresql\_v2\_cluster\_master\_password) | The database master password |
| <a name="output_aurora_postgresql_v2_cluster_master_username"></a> [aurora\_postgresql\_v2\_cluster\_master\_username](#output\_aurora\_postgresql\_v2\_cluster\_master\_username) | The database master username |
| <a name="output_aurora_postgresql_v2_cluster_members"></a> [aurora\_postgresql\_v2\_cluster\_members](#output\_aurora\_postgresql\_v2\_cluster\_members) | List of RDS Instances that are a part of this cluster |
| <a name="output_aurora_postgresql_v2_cluster_port"></a> [aurora\_postgresql\_v2\_cluster\_port](#output\_aurora\_postgresql\_v2\_cluster\_port) | The database port |
| <a name="output_aurora_postgresql_v2_cluster_reader_endpoint"></a> [aurora\_postgresql\_v2\_cluster\_reader\_endpoint](#output\_aurora\_postgresql\_v2\_cluster\_reader\_endpoint) | A read-only endpoint for the cluster, automatically load-balanced across replicas |
| <a name="output_aurora_postgresql_v2_cluster_resource_id"></a> [aurora\_postgresql\_v2\_cluster\_resource\_id](#output\_aurora\_postgresql\_v2\_cluster\_resource\_id) | The RDS Cluster Resource ID |
| <a name="output_aurora_postgresql_v2_cluster_role_associations"></a> [aurora\_postgresql\_v2\_cluster\_role\_associations](#output\_aurora\_postgresql\_v2\_cluster\_role\_associations) | A map of IAM roles associated with the cluster and their attributes |
| <a name="output_aurora_postgresql_v2_db_subnet_group_name"></a> [aurora\_postgresql\_v2\_db\_subnet\_group\_name](#output\_aurora\_postgresql\_v2\_db\_subnet\_group\_name) | The db subnet group name |
