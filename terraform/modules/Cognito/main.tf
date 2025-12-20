resource "aws_cognito_user_pool_domain" "cognito-domain" {
  domain       = "sajilclick"
  user_pool_id = "${aws_cognito_user_pool.pool.id}"
}

resource "aws_cognito_user_pool" "pool" {
    name = "userpool"

    alias_attributes = ["email"]

    password_policy {
        minimum_length    = 8
    }

    auto_verified_attributes = ["email"]

    verification_message_template {
        default_email_option = "CONFIRM_WITH_CODE"
        email_subject = "Verify your email for our app"
        email_message = "Please use the following code to verify your email: {####}"
    }

    schema {
        attribute_data_type = "String"
        name                = "email"
        required            = true
        mutable             = true
    }
}

resource "aws_cognito_user_pool_client" "client" {
  name = "cognito-client"

  user_pool_id = aws_cognito_user_pool.pool.id
  generate_secret = false
  refresh_token_validity = 90
  prevent_user_existence_errors = "ENABLED"
  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH"
  ]
}

resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = "sajilclick"
  allow_unauthenticated_identities = false
  allow_classic_flow               = false

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.client.id
    provider_name           = aws_cognito_user_pool.pool.endpoint
    server_side_token_check = false
  }
}