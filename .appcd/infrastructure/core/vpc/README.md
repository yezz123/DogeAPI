# cafi infrastructure
Core infrastrucutre for the cafi platform.

## Setting local environment for Terraform
Pre-requisites:

    - chtf
    - terraform 1.4.6
    - aws cli

Run the below commands and replace `[hash]` depending on your local environment. Use `default` as the name of the profile when configuring aws access for ease of use.
```sh
# Terraform setup
chtf 1.4.6

# AWS cli setup and credentials
aws sso login
aws configure sso
aws s3 ls

# For AWS SSO to work with terraform you need the below env vars
# Replace [hash] according to your local environment
export AWS_ACCESS_KEY_ID="$(cat ~/.aws/cli/cache/[hash].json |jq -r .Credentials.AccessKeyId)"
export AWS_SECRET_ACCESS_KEY="$(cat ~/.aws/cli/cache/[hash].json |jq -r .Credentials.SecretAccessKey)"
export AWS_SESSION_TOKEN="$(cat ~/.aws/cli/cache/[hash].json |jq -r .Credentials.SessionToken)"
```

## Executing terraform for infrastructure components
A tfvar file is defined for each environment and is located in the [environments](environments) directory.

Below are the terraform commands to use when provisioning the infrastructure. Replace `<infastructure_component>` with the infrastructure component you wish to provision/modify (e.g. RDS, EKS, etc.) and `<environment>` with the environment to provision to.

```sh
cd <infastructure_component>
terraform init
terraform plan -var-file=../environments/<environment>.tfvars -out=tfplan
terraform apply "tfplan" && rm tfplan
```

## Infrastructure component documentation
Under each infrastructure component's directory, the README file will contain additional documentation on what the infrastructure component is and the terraform template used to manage it.
