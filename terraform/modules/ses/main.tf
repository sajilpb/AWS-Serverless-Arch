data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_route53_zone" "this" {
  name = var.domain
}

resource "aws_ses_domain_identity" "this" {
  domain = var.domain
}

resource "aws_route53_record" "ses_verification" {
  zone_id = data.aws_route53_zone.this.zone_id
  name    = "_amazonses.${var.domain}"
  type    = "TXT"
  ttl     = 300
  records = [aws_ses_domain_identity.this.verification_token]
}

resource "aws_ses_domain_identity_verification" "this" {
  domain     = aws_ses_domain_identity.this.domain
  depends_on = [aws_route53_record.ses_verification]
}

resource "aws_route53_record" "mx" {
  zone_id = data.aws_route53_zone.this.zone_id
  name    = var.domain
  type    = "MX"
  ttl     = 300
  records = ["10 inbound-smtp.${data.aws_region.current.name}.amazonaws.com"]
}

resource "aws_ses_receipt_rule_set" "this" {
  rule_set_name = var.rule_set_name
}

resource "aws_ses_active_receipt_rule_set" "this" {
  rule_set_name = aws_ses_receipt_rule_set.this.rule_set_name
}

resource "aws_ses_receipt_rule" "store_in_s3" {
  name          = "store-in-s3"
  rule_set_name = aws_ses_receipt_rule_set.this.rule_set_name
  enabled       = true
  scan_enabled  = true
  tls_policy    = "Optional"

  # Match all recipients at the domain if none provided
  recipients = length(var.recipients) == 0 ? [var.domain] : var.recipients

  s3_action {
    bucket_name                          = var.ses_bucket_name
    object_key_prefix                    = var.object_key_prefix
    position                             = 1
    object_owner_override_to_bucket_owner = true
  }

  depends_on = [aws_ses_domain_identity_verification.this]
}

# Allow Amazon SES to write emails to the S3 bucket
data "aws_iam_policy_document" "ses_put_s3" {
  statement {
    sid     = "AllowSESPuts"
    effect  = "Allow"
    actions = ["s3:PutObject"]

    principals {
      type        = "Service"
      identifiers = ["ses.amazonaws.com"]
    }

    resources = [
      "arn:aws:s3:::${var.ses_bucket_name}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:Referer"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "ses_put" {
  bucket = var.ses_bucket_name
  policy = data.aws_iam_policy_document.ses_put_s3.json
}
