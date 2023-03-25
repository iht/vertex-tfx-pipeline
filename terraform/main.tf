locals {
  services_used = [
    "bigquery.googleapis.com",
    "aiplatform.googleapis.com",
    "dataflow.googleapis.com",
    "monitoring.googleapis.com"
  ]

  apis_to_enable = concat(["accesscontextmanager.googleapis.com"], local.services_used)
}

// Project
module "vx_pl_proj" {
  source          = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/project?ref=v20.0.0"
  billing_account = var.billing_account
  parent          = var.organization
  name            = var.project_id
  project_create  = var.create_project
  services        = local.apis_to_enable
}

// Bucket for staging data, scripts, etc
module "vx_pl_bucket" {
  source        = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/gcs?ref=v20.0.0"
  project_id    = module.vx_pl_proj.project_id
  name          = module.vx_pl_proj.project_id
  location      = var.region
  storage_class = "STANDARD"
  force_destroy = true
}

// BigQuery dataset
module "bigquery-dataset" {
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/bigquery-dataset?ref=v20.0.0"
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
  source       = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/iam-service-account?ref=v20.0.0"
  project_id   = module.vx_pl_proj.project_id
  name         = "ml-in-prod-vertex-sa"
  generate_key = false
  iam          = {
    "roles/iam.serviceAccountUser" = [module.vertex_sa.iam_email]
  }
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
  source       = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/iam-service-account?ref=v20.0.0"
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
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/net-vpc?ref=v20.0.0"
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
  source               = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/net-vpc-firewall?ref=v20.0.0"
  project_id           = module.vx_pl_proj.project_id
  network              = module.vx_pl_vpc.name
  default_rules_config = {
    admin_ranges = [module.vx_pl_vpc.subnet_ips["${var.region}/vertex"]]
  }
}

module "vx_pl_vpc_sc" {
  source               = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/vpc-sc?ref=v20.0.0"
  access_policy        = null
  access_policy_create = {
    parent = var.organization
    title  = "vertex-pipelines-access-policy"
  }
  access_levels = {
    permitted_users = {
      conditions = [{ members = var.users_with_vpc_sc_access }]
    }
  }

  service_perimeters_regular = {
    vertex_pipeline_perimeter = {
      status = {
        access_levels           = ["permitted_users"]
        resources               = ["projects/${module.vx_pl_proj.number}"]
        restricted_services     = local.services_used
        egress_policies         = []
        ingress_policies        = []
        vpc_accessible_services = {
          allowed_services   = ["RESTRICTED-SERVICES"]
          enable_restriction = true
        }
      }
    }
  }
}

resource "google_storage_bucket_object" "data_file" {
  count  = var.create_bq_table == true ? 1 : 0
  bucket = module.vx_pl_bucket.name
  name   = "data/creditcard.csv.gz"
  source = "../data/creditcard.csv.gz"
}

resource "google_bigquery_job" "csv_load_job" {
  count      = var.create_bq_table == true ? 1 : 0
  depends_on = [google_storage_bucket_object.data_file[0]]
  job_id     = "load_csv_data"
  project    = module.vx_pl_proj.project_id
  location   = var.region
  load {
    source_uris = [
      "gs://${google_storage_bucket_object.data_file[0].bucket}/${google_storage_bucket_object.data_file[0].output_name}"
    ]
    destination_table {
      project_id = module.vx_pl_proj.project_id
      dataset_id = module.bigquery-dataset.dataset_id
      table_id   = "transactions"
    }
    autodetect        = true
    source_format     = "CSV"
    write_disposition = "WRITE_TRUNCATE"
  }
}