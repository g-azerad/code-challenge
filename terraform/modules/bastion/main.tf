# Create bastion EC2 VM
resource "aws_instance" "bastion" {
  ami           = var.ami
  instance_type = var.instance_type
  key_name      = var.key_name

  network_interface {
    network_interface_id = var.bastion_eni_id
    device_index         = 0
  }

  tags = {
    Name = var.name
  }
/*
  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get install -y awscli",
      "sudo apt-get install -y iputils-ping"
    ]
  }
*/
}

