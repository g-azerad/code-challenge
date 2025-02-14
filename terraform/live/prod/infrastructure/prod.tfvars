region                     = "eu-west-3"
environment                = "prod"
application_name           = "api-uni"
tf_state_name              = "default"
gitlab_project_id          = "7"
integration_target         = "lambda"
ssh_public_key             = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPXQTe+bt2/WREsoHZxeR/XcZJwlNTaw55G1L/yMRpy3"
db_user_secret_name        = "db_user_secret"
db_master_user_secret_name = "db_master_user_secret"
postgresql_version         = "17.2"
db_allocated_storage       = 20
backup_retention_period    = 7
db_name                    = "uni"
db_master_username         = "postgres"
db_username                = "hoodie"
db_port                    = 5432
ssl_mode                   = "require"
iam_auth                   = "disabled"
display                    = ":99"
debug_mode                 = "true"
lambda_zip_file            = "../../../../app/app_package.zip"
dependencies_package       = "../../../../dependencies_layer.zip"
image_name                 = "975049948125.dkr.ecr.eu-west-3.amazonaws.com/api-uni"
image_tag                  = "latest"
