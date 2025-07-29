module "app" {
  source      = "../.."
  environment = "dev"
  location    = "japaneast"
  app_name    = "chat-sandbox"
}
