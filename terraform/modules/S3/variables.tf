variable "s3bucketname" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "create_bucket" {
  type = bool
  default = true
  
}

variable "upload_to_s3"{
  type = bool
  default = false
}

variable "source_file_path"{
  type = string
  default = ""
}

variable "s3_key" {
  type        = string
  description = "S3 object key for uploaded file"
  default     = "login_redirect.py"
}

variable "output_zip_path" {
  type = string
  default = ""
  
}