data "aws_secretsmanager_random_password" "db_master_user_password" {
  password_length     = var.password_length
  include_space       = false
  exclude_punctuation = true
}

data "aws_secretsmanager_random_password" "db_user_password" {
  password_length     = var.password_length
  include_space       = false
  exclude_punctuation = true
}

resource "aws_secretsmanager_secret" "db_master_user_secret" {
  name        = var.db_master_user_secret_name
  description = "Master user secret for counter database"
  recovery_window_in_days = var.recovery_window
  # force_overwrite_replica_secret = true

  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_secretsmanager_secret" "db_user_secret" {
  name        = var.db_user_secret_name
  description = "Common user secret for counter database"
  recovery_window_in_days = var.recovery_window
  # force_overwrite_replica_secret = true

  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_secretsmanager_secret_version" "db_master_user_password_version" {
  secret_id     = aws_secretsmanager_secret.db_master_user_secret.id
  secret_string = data.aws_secretsmanager_random_password.db_master_user_password.random_password
  lifecycle {
    ignore_changes = [secret_string, ]
  }
}

resource "aws_secretsmanager_secret_version" "db_user_password_version" {
  secret_id     = aws_secretsmanager_secret.db_user_secret.id
  secret_string = data.aws_secretsmanager_random_password.db_user_password.random_password
  lifecycle {
    ignore_changes = [secret_string, ]
  }
}
