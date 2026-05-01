resource "aws_s3_bucket" "b" {
  bucket        = var.s3bucketname
  force_destroy = true

  tags = merge(
    var.tags,
   {
    Name = var.s3bucketname
  }
  )
}

data "archive_file" "lambda_code" {
  count = var.source_file_path != "" ? 1:0
  type = "zip"
  source_dir = var.source_file_path
  output_path = var.output_zip_path
}

# Conditionally upload to S3
resource "aws_s3_object" "code" {
  count  = var.source_file_path != "" ? 1 : 0
  bucket = aws_s3_bucket.b.id
  key    = var.s3_key
  source = data.archive_file.lambda_code[0].output_path
  etag   = data.archive_file.lambda_code[0].output_base64sha256
}



