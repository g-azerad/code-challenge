variable "region" {
  description = "Region of the whole network configuration"
  default = "eu-west-3"
}

variable "availability_zone" {
  description = "Availability Zone for primary resources"
  default = "eu-west-3a"
}

variable "availability_zone_bkp" {
  description = "Availability Zone for backup resources"
  default = "eu-west-3b"
}

variable "name" {
  description = "Infrastructure setup name"
}

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC"
  default = "10.0.0.0/16"
}

variable "enable_dns_support" {
  description = "Enable DNS support for the VPC"
  default = true
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames for the VPC"
  default = true
}

variable "public_subnet_cidr_block" {
  description = "CIDR block for the public subnet"
  default = "10.0.1.0/24"
}

variable "map_public_ip_on_launch" {
  description = "Maps a public IP when launching the public subnet"
  default = true
}

variable "private_subnet_cidr_block" {
  description = "CIDR block for the private subnet"
  default = "10.0.2.0/24"
}

variable "private_subnet_bkp_cidr_block" {
  description = "CIDR block for the backup private subnet"
  default = "10.0.3.0/24"
}

variable "ingress_rules" {
  description = "Inbound rules for security group"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    },
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]
}

variable "bastion_cidr_ipv4" {
  description = "CIDR block for Bastion SSH access"
  type        = string
  default     = "127.0.0.1/32"  # Placeholder IP
}