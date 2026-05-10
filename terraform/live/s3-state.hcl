locals {
  aws_region        = "us-east-1"
  state_bucket_name = get_env("TG_STATE_BUCKET", "sajilpb-aws-serverless-arch-tfstate-test")
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
provider "aws" {
  region = "${local.aws_region}"
}
EOF
}

remote_state {
  backend = "s3"

  config = {
    bucket       = local.state_bucket_name
    key          = "${path_relative_to_include()}/terraform.tfstate"
    region       = local.aws_region
    encrypt      = true
    use_lockfile = true

    s3_bucket_tags = {
      Project   = "AWS-Serverless-Arch"
      ManagedBy = "Terragrunt"
      Temporary = "true"
    }
  }

  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}
