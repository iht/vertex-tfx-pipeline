// Project
module "vx_pl_proj" {
  source          = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/project?ref=v19.0.0"
  billing_account = var.billing_account
  name            = var.project_id
  project_create  = var.create_project
  services        = [
    "bigquery.googleapis.com",
    "aiplatform.googleapis.com",
    "dataflow.googleapis.com",
    "monitoring.googleapis.com",
    "bigquerystorage.googleapis.com",
  ]
}

// Bucket for staging data, scripts, etc
module "vx_pl_bucket" {
  source        = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/gcs?ref=v19.0.0"
  project_id    = module.vx_pl_proj.project_id
  name          = module.vx_pl_proj.project_id
  location      = var.region
  storage_class = "STANDARD"
  force_destroy = true
}

// BigQuery dataset
module "bigquery-dataset" {
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/bigquery-dataset?ref=v19.0.0"
  project_id = module.vx_pl_proj.project_id
  id         = "data_playground"
  location   = var.region // for easy import of data from public datasets
  access     = {
    vertex_sa   = { role = "READER", type = "user" },
    dataflow_sa = { role = "READER", type = "user" }
  }
  access_identities = {
    vertex_sa   = module.vertex_sa.email,
    dataflow_sa = module.dataflow_sa.email,
  }
}

// Service accounts
module "vertex_sa" {
  source            = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/iam-service-account?ref=v19.0.0"
  project_id        = module.vx_pl_proj.project_id
  name              = "ml-in-prod-vertex-sa"
  generate_key      = false
  iam_project_roles = {
    (module.vx_pl_proj.project_id) = [
      "roles/storage.admin",
      "roles/aiplatform.user",
      "roles/bigquery.user",
      "roles/dataflow.admin",
      "roles/monitoring.metricWriter",
    ]
  }
}

module "dataflow_sa" {
  source       = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/iam-service-account?ref=v19.0.0"
  project_id   = module.vx_pl_proj.project_id
  name         = "ml-in-prod-dataflow-sa"
  generate_key = false
  iam          = {
    "roles/iam.serviceAccountUser" = [module.vertex_sa.iam_email]
  }
  iam_project_roles = {
    (module.vx_pl_proj.project_id) = [
      "roles/storage.admin",
      "roles/dataflow.worker",
      "roles/monitoring.metricWriter",
      "roles/bigquery.user"
    ]
  }
}

// Network
module "vx_pl_vpc" {
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/net-vpc?ref=v19.0.0"
  project_id = module.vx_pl_proj.project_id
  name       = "vertexnet"

  subnets = [
    {
      ip_cidr_range         = "10.1.0.0/24"
      name                  = "vertex"
      region                = var.region
      enable_private_access = true
    }
  ]
}

module "vx_pl_firewall" {
  // Default rules for internal traffic + SSH access via IAP
  source               = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/net-vpc-firewall?ref=v19.0.0"
  project_id           = module.vx_pl_proj.project_id
  network              = module.vx_pl_vpc.name
  default_rules_config = {
    admin_ranges = [module.vx_pl_vpc.subnet_ips["${var.region}/vertex"]]
  }
}

module "vx_pl_nat" {
  // So we can get to Internet if necessary
  source         = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/net-cloudnat?ref=v19.0.0"
  project_id     = module.vx_pl_proj.project_id
  region         = var.region
  name           = "default"
  router_network = module.vx_pl_vpc.self_link
}