variable "s3bucketname" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}