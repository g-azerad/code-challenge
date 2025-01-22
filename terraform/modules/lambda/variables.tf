variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

variable "api_name" {
  description = "Name of the API"
  type        = string
}

variable "public_subnet_id" {
  description = "Public subnet id for the Lambda."
  type        = string
}

variable "security_group_id" {
  description = "Security Group id for the Lambda."
  type        = string
}

variable "lambda_zip_file" {
  description = "Path to the ZIP file containing the Lambda function code"
  type        = string
  // default     = "../../../../app_package.zip"
}

variable "lambda_handler" {
  description = "Handler for the Lambda function"
  type        = string
  default     = "app.handler"
}

variable "lambda_runtime" {
  description = "Runtime for the Lambda function"
  type        = string
  default     = "python3.12"
}

variable "dependencies_package" {
  description = "Dependencies zipped package"
  type        = string
  // default     = "../../../../dependencies_layer.zip"
}

variable "db_user_secret_name" {
  description = "Name of the database secret in AWS Secrets Manager"
  type        = string
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "counter_db"
}

variable "db_username" {
  description = "Main username for the database"
  type        = string
  default     = "userdb"
}

variable "db_port" {
  description = "Port to access the database"
  type        = number
  default     = 5432
}

variable "db_host" {
  description = "Host address where the database is running"
  type        = string
}

variable "display" {
  description = "Screen display value used to run the application"
  type        = string
  default     = ":99"
}

variable "api_gateway_execution_arn" {
  description = "API gateway execution ARN for the Lambda permission"
  type        = string
}

variable "db_connect_iam_policy_arn" {
  description = "ARN of the IAM policy to connect to the RDS database"
  type        = string
}