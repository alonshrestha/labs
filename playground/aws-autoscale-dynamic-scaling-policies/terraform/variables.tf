
variable "ami" {
  description = "AMI ID"
  type        = string
}

variable "instanceProfile" {
  description = "IAM Instance Profile ARN"
  type        = string
}

variable "instanceType" {
  description = "EC2 Instance Type"
  type        = string
}

variable "subnetsId" {
  description = "list of subnet IDs"
  type        = list(string)
}

variable "availabilityZones" {
  description = "list of availability zones"
  type        = list(string)
}

variable "tags" {
  description = "Tags"
  type = map(string)
}