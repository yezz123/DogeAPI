# EKS
Infrastructure templates for managing the EKS cluster.

Note: There were some manual steps performed at the moment to make the ALB controller work which are captured as comments on the main.tf and were taken from:

- https://docs.aws.amazon.com/eks/latest/userguide/alb-ingress.html
- https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.13.1 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 4.9 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_terraform"></a> [terraform](#provider\_terraform) | n/a |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_eks"></a> [eks](#module\_eks) | terraform-aws-modules/eks/aws | ~> 19.5 |

## Resources

| Name | Type |
|------|------|
| [terraform_remote_state.vpc](https://registry.terraform.io/providers/hashicorp/terraform/latest/docs/data-sources/remote_state) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | AWS region | `any` | n/a | yes |
| <a name="input_cluster_name"></a> [cluster\_name](#input\_cluster\_name) | Cluster name | `string` | `"cafi"` | no |
| <a name="input_cluster_version"></a> [cluster\_version](#input\_cluster\_version) | n/a | `string` | `"1.24"` | no |
| <a name="input_environment"></a> [environment](#input\_environment) | Environment name | `any` | n/a | yes |
| <a name="input_state_bucket_name"></a> [state\_bucket\_name](#input\_state\_bucket\_name) | State bucket name | `string` | `"cafi-dev-state-bucket"` | no |
| <a name="input_state_bucket_region"></a> [state\_bucket\_region](#input\_state\_bucket\_region) | State bucket region | `string` | `"us-east-1"` | no |
| <a name="input_state_bucket_vpc_key"></a> [state\_bucket\_vpc\_key](#input\_state\_bucket\_vpc\_key) | State bucket VPC key | `string` | `"cafi-dev/cafi/infrastructure/vpc/terraform.tfstate"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_cluster_arn"></a> [cluster\_arn](#output\_cluster\_arn) | n/a |
| <a name="output_cluster_name"></a> [cluster\_name](#output\_cluster\_name) | n/a |
