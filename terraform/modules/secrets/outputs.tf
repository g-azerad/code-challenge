output "db_master_user_secret_arn" {
  description = "Master user database secret ARN into Secrets Manager"
  value       = aws_secretsmanager_secret.db_master_user_secret.arn
}

output "db_master_user_secret_id" {
  description = "Master user database secret id into Secrets Manager"
  value       = aws_secretsmanager_secret.db_master_user_secret.id
}

output "db_user_secret_arn" {
  description = "User database secret ARN into Secrets Manager"
  value       = aws_secretsmanager_secret.db_user_secret.arn
}

output "db_user_secret_id" {
  description = "User database secret id into Secrets Manager"
  value       = aws_secretsmanager_secret.db_user_secret.id
}
