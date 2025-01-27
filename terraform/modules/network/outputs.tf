output "vpc_id" {
  value = aws_vpc.main_vpc.id
}

output "public_subnet_id" {
  value = aws_subnet.public_subnet.id
}

output "public_subnet_cidr" {
  value = var.public_subnet_cidr_block
}

output "private_subnet_id" {
  value = aws_subnet.private_subnet.id
}

output "private_subnet_bkp_id" {
  value = aws_subnet.private_subnet_bkp.id
}

output "instance_sg_id" {
  value = aws_security_group.instance_sg.id
}

output "database_sg_id" {
  value = aws_security_group.database_sg.id
}

output "bastion_sg_id" {
  value = aws_security_group.bastion_sg.id
}

output "bastion_sg_ingress_id" {
  value = aws_vpc_security_group_ingress_rule.bastion_sg_ingress.security_group_rule_id
}

output "bastion_eni_id" {
  value = aws_network_interface.bastion_eni.id
}

output "bastion_eip_id" {
  value = aws_eip.bastion_eip.id
}

output "bastion_public_ip" {
  value = aws_eip.bastion_eip.public_ip
}