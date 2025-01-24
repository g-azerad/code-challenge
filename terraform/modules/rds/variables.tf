variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "counter_db"
}

variable "db_master_username" {
  description = "Master username for the database"
  type        = string
  default     = "user_db"
}

variable "db_port" {
  description = "Port to access the database"
  type        = number
  default     = 5432
}

variable "vpc_id" {
  description = "VPC id where RDS instance is created"
  type        = string
}

variable "security_group_id" {
  description = "Security group id to apply to database"
  type        = string
}

variable "private_subnet_ids" {
  description = "Subnet list for RDS instance"
  type        = list(string)
}

variable "db_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Storage size allocated (Gb)."
  type        = number
  default     = 20
}

variable "engine_version" {
  description = "PostgreSQL version."
  type        = string
  default     = "17.2"
}

variable "backup_retention_period" {
  description = "Back-up retention period (days)."
  type        = number
  default     = 7
}

variable "db_master_user_secret_name" {
  description = "Name of the database secret in AWS Secrets Manager for db master user"
  type        = string
}

variable "public_subnet_ip_range" {
  description = "IP range from public subnet containg the app"
  type        = string
  default     = "10.1.0.0/24"
}

variable "region" {
  description = "Region where infrastructure is created"
  default     = "eu-west-3"
} 

variable "account_id" {
  description = "AWS account id where infrastructure is created"
  type        = string
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot when deleting the database"
  type        = bool
  default     = true
}
