variable "password_length" {
  description = "Password length"
  type        = number
  default     = 32
}

variable "recovery_window" {
  description = "Recovery windows for the secret (in days)"
  type        = number
  default     = 7
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