ami = "ami-xxxxxxxxx"
instanceProfile = "arn:aws:iam::123123123123:instance-profile/your-instance-profile"
instanceType = "t3a.micro"
subnetsId = ["subnet-xxxxx", "subnet-xxxx"]
availabilityZones = ["us-east-1a", "us-east-1b"]
tags = {
      Name               = "Ec2AutoScalingDemo"
      ManagedBy          = "Terraform"
    }