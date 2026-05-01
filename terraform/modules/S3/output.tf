output "bucket_name" {
  value = aws_s3_bucket.b.bucket
}

output "bucket_name_arn" {
  value = aws_s3_bucket.b.arn
}

output "s3_key" {
  value       = var.source_file_path != "" ? aws_s3_object.code[0].key : ""
  description = "S3 object key (empty if no upload)"
}

output "etag" {
  value       = var.source_file_path != "" ? aws_s3_object.code[0].etag : ""
  description = "S3 object etag (empty if no upload)"
}