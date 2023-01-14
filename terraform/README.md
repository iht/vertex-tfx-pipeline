# Terraform code for Vertex project

Use this code to create a project in Google Cloud to run the Vertex pipeline.

Configure the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install-sdk) 
with an account that can create projects (or the owner of an existing 
project), and run this to authenticate for Terraform:

```shell
export GOOGLE_OAUTH_ACCESS_TOKEN=`gcloud auth print-access-token`
```

## Variables

Create a file called `terraform.tfvars` with the right values. For instance, 
to reuse an existing project, use values similar to these ones:

```hcl
region          = "us-central1"
billing_account = "1234-1234-1234-1234"
project_id      = "my-vertex-project"
```

Check the file `terraform.tfvars.sample` for an example. You can copy it to 
`terraform.tfvars` and edit it for more convenience.

## Prepare project

This repository assumes that there is a BigQuery table with certain data, a 
couple of service accounts, a network with Google Private Access, etc. To 
setup an existing Google Cloud project to be ready for this pipeline, run

```shell
terraform init
```

and then

```shell
terraform apply
```

## Import data

The directory `data/` contains a CSV file that you need to import as table 
in BigQuery in the dataset `data_playground`.

The Terraform code creates a bucket with the same name as your project id. 

[Upload the CSV to that bucket](https://cloud.google.com/storage/docs/uploading-objects) 
and [import it in BigQuery](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-csv). 

Import it into a table of name `transactions`.

You can use the automatic detection of schema and import the gzipped file 
without having to uncompress it. 