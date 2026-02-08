# Terraform Variables Reference

This page documents key input variables defined in `terraform/variables.tf`.

> Note: This is a high‑level description. Always refer to the actual `variables.tf` file for the authoritative list and defaults.

## Core Variables

- **`s3bucketname`**
  - Type: `string`
  - Description: Name of the S3 bucket used for hosting the frontend.
  - Notes: Must be globally unique across AWS.

- **`cognito_domain_prefix`**
  - Type: `string`
  - Description: Domain prefix for the Cognito Hosted UI (e.g., `myapp-dev`).

- **`source_file_path`**
  - Type: `string`
  - Description: Path to the Lambda source code directory or file used for packaging.

- **`output_zip_path`**
  - Type: `string`
  - Description: Destination path for the built Lambda deployment package (ZIP file).

## How to View All Variables

From the `terraform/` directory, inspect `variables.tf` directly or use `terraform console` to experiment with defaults and derived values.
