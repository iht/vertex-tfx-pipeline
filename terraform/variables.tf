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

variable "create_bq_table" {
  description = "Whether to create the BQ table. Set to false if already created and running this TF code again."
  type        = bool
}

variable "organization" {
  description = "Parent for VPC SC access policy"
  type        = string
}

variable "project_id" {
  description = "Id for the project to be created"
  type        = string
}

variable "region" {
  description = "The region for resources and networking"
  type        = string
}

variable "users_with_vpc_sc_access" {
  description = "List of users with access to VPC SC, with IAM-style addresses"
  type        = list(string)
}