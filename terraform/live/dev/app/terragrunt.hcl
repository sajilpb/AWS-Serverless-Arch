include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../"
}

inputs = {
    s3bucketname = "dev-froneendtwebsite2026"
    ses_bucket_name = "dev-froneendtwebsite2026ses"
  source_file_path = "${get_terragrunt_dir()}/../../../../Backend"
    output_zip_path = "./build/login_redirect.zip"
    cognito_domain_prefix = "dev-sajilclick"
  my_domain = "dev.sajil.click"
    certificate_domain = "sajil.click"
}