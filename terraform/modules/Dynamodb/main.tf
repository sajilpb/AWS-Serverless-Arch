resource "aws_dynamodb_table" "user_ec2_instances" {
  name         = "InstanceManagementTable"
  billing_mode = "PAY_PER_REQUEST"

  # Primary key: one user can have many instances
  hash_key  = "user_id"      # Cognito sub
  range_key = "instance_id"  # EC2 instance ID

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "instance_id"
    type = "S"
  }

  # Optional, but useful attributes (no need to declare unless they are keys/GSIs)
  # created_at, region, instance_type, state can be added at write time from Lambda.

  tags = {
    Name        = "user-ec2-instances"
    Environment = "production"
  }
}