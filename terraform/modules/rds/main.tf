data "aws_secretsmanager_secret" "db_master_user_secret" {
  name = var.db_master_user_secret_name
}

data "aws_secretsmanager_secret_version" "db_master_user_secret_version" {
  secret_id = data.aws_secretsmanager_secret.db_master_user_secret.id
}

resource "aws_db_instance" "postgresql" {
  allocated_storage      = var.allocated_storage
  instance_class         = var.db_instance_class
  engine                 = "postgres"
  engine_version         = var.engine_version
  db_name                = var.db_name
  username               = var.db_master_username
  password               = data.aws_secretsmanager_secret_version.db_master_user_secret_version.secret_string
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [var.security_group_id]
  multi_az               = false
  publicly_accessible    = false
  backup_retention_period = var.backup_retention_period
  storage_encrypted      = true
  kms_key_id             = null
  skip_final_snapshot    = var.skip_final_snapshot
  iam_database_authentication_enabled = true
}

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "${var.db_name}-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.db_name}-subnet-group"
  }
}

resource "aws_iam_policy" "rds_iam_connect_policy" {
  name        = "${var.db_name}-iam-connect-policy"
  description = "Policy for IAM Authentication to connect to RDS"
  policy      = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = "rds-db:connect"
        Effect   = "Allow"
        Resource = "arn:aws:rds-db:${var.region}:${var.account_id}:dbuser:${aws_db_instance.postgresql.resource_id}/iam_user"
      }
    ]
  })
}

resource "aws_iam_user" "db_user" {
  name = "${var.db_name}-iam-user"
}

resource "aws_iam_user_policy_attachment" "user_attach_policy" {
  user       = aws_iam_user.db_user.name
  policy_arn = aws_iam_policy.rds_iam_connect_policy.arn
}