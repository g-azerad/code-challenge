output "db_endpoint" {
  description = "PostgreSQL RDS instance endpoint."
  value       = aws_db_instance.postgresql.endpoint
}

output "db_host" {
  description = "PostgreSQL RDS instance host."
  value       = aws_db_instance.postgresql.address
}

output "db_connect_iam_policy_arn" {
  value = aws_iam_policy.rds_iam_connect_policy.arn
}