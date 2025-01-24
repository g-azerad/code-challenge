variable "subnet_id" {
  description = "The subnet ID for the Bastion instance."
  type        = string
}

variable "bastion_sg_id" {
  description = "The ID of the security group associated with the Bastion."
  type        = string
}

variable "bastion_eni_id" {
  description = "The ID of the network interface associated with the Bastion."
  type        = string
}

variable "ami" {
  description = "AMI ID for the instance"
  type        = string
  default     = "ami-087da76081e7685da"
}

variable "instance_type" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "SSH key name to access the EC2 instance"
  type        = string
}

variable "name" {
  description = "Name to tag the bastion VM"
  type        = string
}