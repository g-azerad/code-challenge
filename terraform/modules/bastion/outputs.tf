output "bastion_instance_id" {
  description = "The ID of the Bastion instance"
  value       = aws_instance.bastion.id
}

output "bastion_public_ip" {
  description = "The public IP of the Bastion instance"
  value       = aws_instance.bastion.public_ip
}

output "bastion_private_ip" {
  description = "The private IP of the Bastion instance"
  value       = aws_instance.bastion.private_ip
}