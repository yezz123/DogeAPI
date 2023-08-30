terraform {
  required_version = "~> 1.5.6"

  backend "s3" {
    bucket   = "cafi-demo1"
    key      = "demos/core/eks/terraform.tfstate"
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

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.5"

  cluster_name                   = "${var.cluster_name}-${var.environment}"
  cluster_version                = var.cluster_version
  cluster_endpoint_public_access = true

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnets

  # EKS Addons
  cluster_addons = {
    coredns = {
      configuration_values = jsonencode({
        computeType = "Fargate"
        # Ensure that the we fully utilize the minimum amount of resources that are supplied by
        # Fargate https://docs.aws.amazon.com/eks/latest/userguide/fargate-pod-configuration.html
        # Fargate adds 256 MB to each pod's memory reservation for the required Kubernetes
        # components (kubelet, kube-proxy, and containerd). Fargate rounds up to the following
        # compute configuration that most closely matches the sum of vCPU and memory requests in
        # order to ensure pods always have the resources that they need to run.
        resources = {
          limits = {
            cpu = "0.25"
            # We are targetting the smallest Task size of 512Mb, so we subtract 256Mb from the
            # request/limit to ensure we can fit within that task
            memory = "256M"
          }
          requests = {
            cpu = "0.25"
            # We are targetting the smallest Task size of 512Mb, so we subtract 256Mb from the
            # request/limit to ensure we can fit within that task
            memory = "256M"
          }
        }
      })
    }
    kube-proxy = {}
    vpc-cni    = {}
  }

  # Fargate profiles use the cluster primary security group so these are not utilized
  create_cluster_security_group = false
  create_node_security_group    = false

  fargate_profiles = merge(
    { for i in range(3) :
      "kube-system-${element(split("-", var.azs[i]), 2)}" => {
        selectors = [
          { namespace = "kube-system" }
        ]
        # We want to create a profile per AZ for high availability
        subnet_ids = [element(var.private_subnets, i)]
      }
    },
  )

  tags = local.tags
}

# This provider block provides authentication details to Terraform so that it can
# communicate with the EKS cluster. This provider block uses the AWS CLI to
# fetch the authentication token.

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    # This requires the awscli to be installed locally where Terraform is executed
    args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}


// This code creates a Helm provider that is configured to connect to an EKS cluster.
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      # This requires the awscli to be installed locally where Terraform is executed
      args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

// Add the IAM role for load balancer *Not used right now*
module "vpc_cni_irsa_role" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"

  role_name                              = "load_balancer_controller"
  attach_load_balancer_controller_policy = true

  attach_vpc_cni_policy = true
  vpc_cni_enable_ipv4   = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["default:dogeapi", "canary:dogeapi"]
    }
  }
}

#############
## Manually executed for now after terraform apply
#############

## Intall the AWS Load Balancer Controller
# curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.5.4/docs/install/iam_policy.json

# aws iam create-policy \
#     --policy-name AWSLoadBalancerControllerIAMPolicy \
#     --policy-document file://iam_policy.json \
#     --profile=atlantis-access \
#     --region=us-east-2

# eksctl create iamserviceaccount \
#   --cluster=demo-demo \
#   --namespace=kube-system \
#   --name=aws-load-balancer-controller \
#   --role-name AmazonEKSLoadBalancerControllerRole \
#   --attach-policy-arn=arn:aws:iam::180217099948:policy/AWSLoadBalancerControllerIAMPolicy \
#   --approve \
#   --profile=atlantis-access \
#   --region=us-east-2

# helm repo add eks https://aws.github.io/eks-charts

# helm repo update eks

# helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
#   -n kube-system \
#   --set clusterName=demo-demo \
#   --set serviceAccount.create=false \
#   --set serviceAccount.name=aws-load-balancer-controller \
#   --set region=us-east-2 \
#   --set vpcId=vpc-0c37ffe0affae162f

# kubectl get deployment -n kube-system aws-load-balancer-controller

#############
## Test app to check ALB is working as expected
#############
# eksctl create fargateprofile \
#     --cluster demo-demo \
#     --region us-east-2 \
#     --name alb-sample-app \
#     --namespace game-2048 \
#     --profile=atlantis-access \
#     --region=us-east-2

# kubectl apply -f 2048_full.yaml

# kubectl get ingress/ingress-2048 -n game-2048

## To Debug
# kubectl logs -f -n kube-system -l app.kubernetes.io/instance=aws-load-balancer-controller

# eksctl create fargateprofile \
#     --cluster demo-demo \
#     --region us-east-2 \
#     --name demo-default \
#     --namespace default \
#     --profile=atlantis-access \
#     --region=us-east-2
