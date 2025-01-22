output "ecs_lb_uri" {
  value = "http://${aws_lb.ecs_nlb.dns_name}"
}

output "ecs_vpc_link_id" {
  value = aws_api_gateway_vpc_link.vpc_link.id
}