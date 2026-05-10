#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${TG_APP_DIR:-terraform/live/dev/app}"
STATE_BUCKET="${TG_STATE_BUCKET:-sajilpb-aws-serverless-arch-tfstate-test}"

export TG_REMOTE_STATE_BACKEND="s3"
export TG_STATE_BUCKET="${STATE_BUCKET}"

echo "Using Terragrunt unit: ${APP_DIR}"
echo "Using temporary S3 state bucket: ${TG_STATE_BUCKET}"

cd "${APP_DIR}"

terragrunt backend bootstrap --non-interactive
terragrunt init -migrate-state -force-copy
terragrunt apply "$@"
