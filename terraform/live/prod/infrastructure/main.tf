terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
  backend "http" {
    address        = "https://gitlab.perso.com/api/v4/projects/6/terraform/state/${var.tf_state_name}"
    lock_address   = "https://gitlab.perso.com/api/v4/projects/6/terraform/state/${var.tf_state_name}/lock"
    unlock_address = "https://gitlab.perso.com/api/v4/projects/6/terraform/state/${var.tf_state_name}/lock"
  }
  required_version = ">= 1.10.0"
}

# Getting AWS provider configuration from variables
provider "aws" {
  region                   = var.region
}

# Retrieving account information
data "aws_caller_identity" "current" {}

# Defining the SSH key to use with EC2 instances
resource "aws_key_pair" "access_key" {
  key_name   = "access_key"
  public_key = var.ssh_public_key
}

# Get server public IP to set Bastion SSH access
data "external" "config" {
  program = ["../../../scripts/get_public_ip.sh"]
}

# Importing network module to create network configuration
module "network" {
  source = "../../../modules/network"
  name   = "${var.application_name}-${var.environment}"
}

# Setting the ingress rule for bastion SSH access
resource "aws_vpc_security_group_ingress_rule" "bastion_sg" {
  security_group_id = module.network.bastion_sg_id

  from_port   = 22
  to_port     = 22
  ip_protocol = "tcp"
  cidr_ipv4   = "${data.external.config.result["public_ip"]}/32"
}

# Creating the SSH bastion
module "bastion" {
  source = "../../../modules/bastion"
  subnet_id         = module.network.public_subnet_id
  bastion_sg_id     = module.network.bastion_sg_id
  name              = "${var.application_name}-${var.environment}-bastion"
  key_name          = aws_key_pair.access_key.key_name
  bastion_eni_id    = module.network.bastion_eni_id
}

# Importing rds module to create RDS PostgreSQL database
module "rds" {
  source                     = "../../../modules/rds"
  region                     = var.region
  vpc_id                     = module.network.vpc_id
  security_group_id          = module.network.database_sg_id
  private_subnet_ids         = [module.network.private_subnet_id, module.network.private_subnet_bkp_id]
  allocated_storage          = var.db_allocated_storage
  engine_version             = var.postgresql_version
  backup_retention_period    = var.backup_retention_period
  db_name                    = var.db_name
  db_master_username         = var.db_master_username
  db_port                    = var.db_port
  db_master_user_secret_name = var.db_master_user_secret_name
  public_subnet_ip_range     = module.network.public_subnet_cidr
  account_id                 = data.aws_caller_identity.current.account_id
}

# Creating the Lambda to run the API
module "lambda" {
  source                    = "../../../modules/lambda"
  region                    = var.region
  api_name                  = "${var.application_name}-${var.environment}"
  public_subnet_id          = module.network.public_subnet_id
  security_group_id         = module.network.instance_sg_id
  db_user_secret_name       = var.db_user_secret_name
  db_name                   = var.db_name
  db_username               = var.db_username
  db_port                   = var.db_port
  db_host                   = module.rds.db_host
  display                   = var.display
  api_gateway_execution_arn = module.api_gateway.api_gateway_execution_arn
  db_connect_iam_policy_arn = module.rds.db_connect_iam_policy_arn
}

# Creates the ECS instance running API container if integration target is "ecs"
module "ecs" {
  source                    = "../../../modules/ecs"
  region                    = var.region
  secrets_iam_policy_arn    = module.lambda.secrets_iam_policy_arn
  db_connect_iam_policy_arn = module.rds.db_connect_iam_policy_arn
  ecs_service_name          = "${var.application_name}-${var.environment}-ecs"
  count                     = (var.integration_target == "ecs" ? 1 : 0)
  vpc_id                    = module.network.vpc_id
  image_name                = var.image_name
  image_tag                 = var.image_tag
  public_subnet_id          = module.network.public_subnet_id
  security_group_id         = module.network.instance_sg_id
  db_user_secret_name       = var.db_user_secret_name
  db_name                   = var.db_name
  db_username               = var.db_username
  db_port                   = var.db_port
  db_host                   = module.rds.db_host
  ssl_mode                  = var.ssl_mode
  ssl_root_cert             = local.ssl_root_cert
  iam_auth                  = var.iam_auth
  debug_mode                = var.debug_mode
}

# Creating the API gateway
module "api_gateway" {
  source               = "../../../modules/api_gateway"
  api_name             = "${var.application_name}-${var.environment}"
  integration_target   = var.integration_target
  lambda_invoke_arn    = (var.integration_target == "lambda" ? module.lambda.lambda_invoke_arn : null)
  ecs_vpc_link_id      = (var.integration_target == "ecs" ? module.ecs[0].ecs_vpc_link_id : null)
  ecs_lb_uri           = (var.integration_target == "ecs" ? module.ecs[0].ecs_lb_uri : null)
}