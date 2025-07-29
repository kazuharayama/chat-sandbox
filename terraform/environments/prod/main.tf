module "app" {
  source      = "../.."
  environment = "prod"
  location    = "japaneast"
  app_name    = "chat-sandbox"
}
