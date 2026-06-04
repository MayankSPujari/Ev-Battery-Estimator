terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  alias  = "us-east"
  region = "us-east-1"
}

provider "aws" {
  alias  = "eu-west"
  region = "eu-west-1"
}

module "eks_us_east" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = "ev-mlops-us-east"
  cluster_version = "1.28"
  providers = {
    aws = aws.us-east
  }
}

module "eks_eu_west" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = "ev-mlops-eu-west"
  cluster_version = "1.28"
  providers = {
    aws = aws.eu-west
  }
}
