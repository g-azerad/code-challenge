output "secrets_iam_policy_arn" {
  value = aws_iam_policy.lambda_secrets_policy.arn
}

output "lambda_arn" {
  value = aws_lambda_function.lambda.arn
}

output "lambda_invoke_arn" {
  value = aws_lambda_function.lambda.invoke_arn
}