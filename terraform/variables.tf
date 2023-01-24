variable "billing_account" {
  description = "Billing account for the projects/resources"
  type        = string
  default     = null
}

variable "create_project" {
  description = "Set to false if your project already exists"
  type        = bool
  default     = false
}

variable "organization_or_folder" {
  description = "Parent for the project. Set this if create_project is true"
  type        = string
  default     = null
}

variable "project_id" {
  description = "Id for the project to be created"
  type        = string
}

variable "region" {
  description = "The region for resources and networking"
  type        = string
}


