# Load Balancer (NLB recommended for VPC Links with REST API Gateway)
resource "aws_lb" "ecs_nlb" {
  name               = "${var.ecs_service_name}-nlb"
  internal           = false
  load_balancer_type = "network"
  subnets            = [var.public_subnet_id]

  tags = {
    Name = "${var.ecs_service_name}-nlb"
  }
}

# Target group for ECS
resource "aws_lb_target_group" "ecs_target_group" {
  name        = "${var.ecs_service_name}-tg"
  port        = 80
  protocol    = "TCP"
  vpc_id      = var.vpc_id
  target_type = "ip" # required for Fargate

  health_check {
    protocol            = "HTTP"
    path                = "/healthcheck"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${var.ecs_service_name}-tg"
  }
}

# Listener to direct the trafic to the target group
resource "aws_lb_listener" "ecs_listener" {
  load_balancer_arn = aws_lb.ecs_nlb.arn
  port              = 80
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_target_group.arn
  }
}

# IAM role for ECS task
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.ecs_service_name}-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Attach existing IAM policy to access secrets manager
resource "aws_iam_role_policy_attachment" "task_role_secrets_manager_access" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = var.secrets_iam_policy_arn
}

# Attach RDS db connection policy to the task role
resource "aws_iam_role_policy_attachment" "task_role_db_access" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = var.db_connect_iam_policy_arn
}

# Define IAM role policy for ECS tasks
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.ecs_service_name}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Add an IAM policy to access CloudWatch logs
resource "aws_iam_role_policy_attachment" "ecs_cloudwatch_logs_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# Create a CloudWatch log group
resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name              = "/ecs/${var.ecs_service_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.ecs_service_name}-log-group"
  }
}

/*
# Retrieving database password
data "aws_secretsmanager_secret" "db_user_secret" {
  name = var.db_user_secret_name
}

data "aws_secretsmanager_secret_version" "db_user_secret_version" {
  secret_id = data.aws_secretsmanager_secret.db_user_secret.id
}
*/

# Create an ECS cluster
resource "aws_ecs_cluster" "ecs_cluster" {
  name = "${var.ecs_service_name}-cluster"
}

# Create an ECS task (exposes the API on port 80)
resource "aws_ecs_task_definition" "ecs_task" {
  family                = "${var.ecs_service_name}-task"
  network_mode          = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu       = 256
  memory    = 512
  execution_role_arn    = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn         = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name      = "${var.application_name}-container"
    image     = "${var.image_name}:${var.image_tag}"
    cpu       = 256
    memory    = 512
    essential = true
    portMappings = [{
      containerPort = 80
      hostPort      = 80
      protocol      = "tcp"
    }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/ecs/${var.ecs_service_name}"
        awslogs-region        = var.region
        awslogs-stream-prefix = "ecs"
      }
    }
    environment = [
      {
        name  = "FLASK_ENV"
        value = "production"
      },
      {
        name  = "FLASK_PORT"
        value = "80"
      },
      {
        name  = "DEBUG_MODE"
        value = var.debug_mode
      },
      {
        name  = "DB_USER"
        value = var.db_username
        # value = "iam_user"
      },
      {
        name  = "DB_HOST"
        value = var.db_host
      },
      {
        name  = "DB_PORT"
        value = tostring(var.db_port)
      },
      {
        name  = "DB_NAME"
        value = var.db_name
      },
      {
        name  = "SSL_MODE"
        value = var.ssl_mode
      },
      {
        name  = "SSL_ROOT_CERT"
        value = var.ssl_root_cert
      },
      {
        name  = "DB_USER_SECRET"
        value = var.db_user_secret_name
      },
      {
        name  = "IAM_AUTH"
        value = var.iam_auth
      }/*,
      {
        name  = "DB_PASSWORD"
        value = data.aws_secretsmanager_secret_version.db_user_secret_version.secret_string
      }*/
    ]
  }])
}

# Define an ECS service which targets the cluster and the ECS task
resource "aws_ecs_service" "ecs_service" {
  name            = var.ecs_service_name
  cluster         = aws_ecs_cluster.ecs_cluster.id
  task_definition = aws_ecs_task_definition.ecs_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  enable_execute_command = true

  network_configuration {
    subnets          = [var.public_subnet_id]
    security_groups = [var.security_group_id]
    assign_public_ip = true # Required to download images from Docker Hub
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ecs_target_group.arn
    container_name   = "${var.application_name}-container"
    container_port   = 80
  }
}

# Create a VPC Link for API Gateway
resource "aws_api_gateway_vpc_link" "vpc_link" {
  name         = "${var.ecs_service_name}-vpc-link"
  target_arns  = [aws_lb.ecs_nlb.arn]
  description  = "VPC Link to ECS service"
}
