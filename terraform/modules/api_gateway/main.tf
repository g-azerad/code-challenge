resource "aws_api_gateway_rest_api" "api_gateway" {
  name          = var.api_name
}

# Generic resource /{proxy+}
resource "aws_api_gateway_resource" "api_proxy" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  parent_id   = aws_api_gateway_rest_api.api_gateway.root_resource_id
  path_part   = "{proxy+}"
}

# ANY method for /counter endpoint and all the subpaths
resource "aws_api_gateway_method" "proxy_any" {
  rest_api_id   = aws_api_gateway_rest_api.api_gateway.id
  resource_id   = aws_api_gateway_resource.api_proxy.id
  http_method   = "ANY"
  authorization = "NONE"

  # To transmit the path to the integration for ECS
  request_parameters = var.integration_target == "ecs" ? {
    "method.request.path.proxy" = true
  } : null
}

# The API integration depends from the target (lambda or ECS)
resource "aws_api_gateway_integration" "api_integration" {
  rest_api_id             = aws_api_gateway_rest_api.api_gateway.id
  resource_id             = aws_api_gateway_resource.api_proxy.id
  http_method             = aws_api_gateway_method.proxy_any.http_method
  passthrough_behavior    = "WHEN_NO_MATCH"
  type                    = var.integration_target == "lambda" ? "AWS_PROXY" : "HTTP_PROXY"
  integration_http_method = var.integration_target == "lambda" ? "POST" : "ANY"
  uri                     = var.integration_target == "lambda" ? var.lambda_invoke_arn : "${var.ecs_lb_uri}/{proxy}"
  connection_type         = var.integration_target == "ecs" ? "VPC_LINK" : null
  connection_id           = var.integration_target == "ecs" ? var.ecs_vpc_link_id : null
  # Transmit the path and the method to the integration for ECS
  request_parameters = var.integration_target == "ecs" ? {
    "integration.request.header.X-HTTP-Method" = "context.httpMethod"
    "integration.request.path.proxy" = "method.request.path.proxy"
  } : null
}

# Defining deployment with logging enabled

resource "aws_api_gateway_deployment" "deployment" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  depends_on = [
    aws_api_gateway_integration.api_integration
  ]
}

resource "aws_api_gateway_stage" "api_stage" {
  rest_api_id           = aws_api_gateway_rest_api.api_gateway.id
  deployment_id         = aws_api_gateway_deployment.deployment.id
  stage_name            = "prod"
  description           = "Production stage"
  cache_cluster_enabled = false

  depends_on    = [aws_cloudwatch_log_group.api_gateway_log_group]
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_log_group.arn
    format = jsonencode({
      requestId        = "$context.requestId"
      requestTime      = "$context.requestTime"
      requestTimeEpoch = "$context.requestTimeEpoch"
      path             = "$context.path"
      method           = "$context.httpMethod"
      status           = "$context.status"
      responseLength   = "$context.responseLength"
    })
  }
}

resource "aws_iam_role" "api_gateway_logs_role" {
  name = "api-gateway-logs-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
        Effect    = "Allow"
        Sid       = ""
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_logs_policy" {
  role       = aws_iam_role.api_gateway_logs_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

resource "aws_cloudwatch_log_group" "api_gateway_log_group" {
  name              = "/api_gateway/${var.api_name}"
  retention_in_days = 7
}

resource "aws_api_gateway_account" "api_gateway_account" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_logs_role.arn
}

resource "aws_api_gateway_method_settings" "proxy_any_settings" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  stage_name  = aws_api_gateway_stage.api_stage.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled = true
    logging_level   = "INFO"
  }
}
