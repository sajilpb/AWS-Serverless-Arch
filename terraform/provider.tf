terraform {
  required_providers {
    aws = {
        source = "hashicorp/aws"
        version = "6.26.0"
    }
    archive = {
        source = "hashicorp/archive"
        version = "2.5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}