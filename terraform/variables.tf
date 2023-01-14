variable "billing_account" {
  description = "Billing account for the projects/resources"
  type        = string
}

variable "create_project" {
  description = "Set to false if your project already exists"
  type        = bool
  default     = false
}

variable "project_id" {
  description = "Id for the project to be created"
  type        = string
}

variable "region" {
  description = "The region for resources and networking"
  type        = string
}


