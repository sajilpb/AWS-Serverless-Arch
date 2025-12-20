resource "aws_s3_bucket" "b" {
  bucket        = var.s3bucketname
  force_destroy = true

  tags = {
    Name = var.s3bucketname
  }
}