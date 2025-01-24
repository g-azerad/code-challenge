variable "environment" {
  type        = string
}

variable "tf_state_name" {
  description = "Terraform state name (used by Gitlab CI)"
  type        = string
  default     = "default"
}

variable "gitlab_project_id" {
  description = "Gitlab project id to setup terraform state"
  type        = string
  default     = "7"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

variable "application_name" {
  type    = string
  default = "api-uni"
}

variable "integration_target" {
  description = "Integration target for the API gateway (lambda or ecs)"
  type        = string
  default     = "lambda"
}

variable "ssh_public_key" {
  description = "The SSH public key to access the EC2 instances."
  type        = string
}

variable "db_master_user_secret_name" {
  description = "Secret name for the database master user"
  type        = string
}

variable "db_user_secret_name" {
  description = "Secret name for the database user"
  type        = string
}

variable "postgresql_version" {
  description = "PostgreSQL version for the database"
  type        = string
}

variable "db_allocated_storage" {
  description = "Allocated storage for the database (GB)"
  type        = number
}

variable "backup_retention_period" {
  description = "Back-up retention period for the database (days)"
  type        = number
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "counter_db"
}

variable "db_master_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
}

variable "db_username" {
  description = "Database username for Lambda"
  type        = string
  default     = "user_db"
}

variable "db_port" {
  description = "Database access port"
  type        = number
  default     = 5432
}

variable "ssl_mode" {
  description = "SSL mode for database connection"
  type        = string
  default     = "require"
}

variable "ssl_root_cert" {
  description = "RDS ssl root path for database connection"
  type        = string
  default     = null
}

locals {
    ssl_root_cert = var.ssl_root_cert == "" ? "/etc/ssl/certs/${var.region}-bundle.pem" : var.ssl_root_cert
}

variable "iam_auth" {
  description = "Enable/disable IAM authentication to the database"
  type        = string
}

variable "display" {
  description = "Screen display value used to run the application"
  type        = string
  default     = ":99"
}

variable "debug_mode" {
  description = "Enable/disable debug mode for Flask application"
  type        = string
  default     = "false"
} 

variable "lambda_zip_file" {
  description = "Lambda application zip file location"
  type        = string
}

variable "dependencies_package" {
  description = "Lambda dependencies package zip file location"
  type        = string
}

variable "image_name" {
  description = "API Docker Hub image name"
  type        = string
  default     = "counter-api"
}

variable "image_tag" {
  description = "API Docker Hub image tag"
  type        = string
  default     = "latest"
}