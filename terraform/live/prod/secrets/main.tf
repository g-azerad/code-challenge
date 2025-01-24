terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }

  required_version = ">= 1.10.0"
}

# Getting AWS provider configuration from variables
provider "aws" {
  region                   = var.region
}

# Importing secrets module to handle the passwords
module "secrets" {
  source                     = "../../../modules/secrets"
  recovery_window            = var.recovery_window
  db_master_user_secret_name = var.db_master_user_secret_name
  db_user_secret_name        = var.db_user_secret_name
}