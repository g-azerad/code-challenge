variable "environment" {
  type        = string
  default     = "prod"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

variable "recovery_window" {
  description = "Number of days for the recovery window of secrets"
  type        = number
  default     = 0
}

variable "db_master_user_secret_name" {
  description = "Secret name for database master user"
  type        = string
  default     = "db_master_user_secret"
}

variable "db_user_secret_name" {
  description = "Secret name for database user"
  type        = string
  default     = "db_user_secret"
}
