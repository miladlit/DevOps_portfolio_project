variable "subscription_id" {
  type        = string
  description = "Azure subscription ID; supply through TF_VAR_subscription_id."
}
variable "location" {
  type    = string
  default = "swedencentral"
}
variable "prefix" {
  type    = string
  default = "service-status"
}
variable "admin_username" {
  type    = string
  default = "deploy"
}
variable "ssh_public_key" {
  type        = string
  description = "SSH public key, never a private key."
}
variable "admin_cidr" {
  type        = string
  description = "Your public IPv4 address with /32; SSH is restricted to this address."
  validation {
    condition     = can(cidrnetmask(var.admin_cidr)) && endswith(var.admin_cidr, "/32")
    error_message = "Use a single administrator IPv4 address with /32."
  }
}
variable "vm_size" {
  type    = string
  default = "Standard_B1s"
}
