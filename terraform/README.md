# Terraform code for Vertex project

Use this code to create a project in Google Cloud to run the Vertex pipeline.

## Using the Cloud Shell 

We recommend using the Cloud Shell with this code (e.g. clone the repo from 
Github in the Cloud Shell), as everything will be already configured 
(Terraform, Google Cloud SDK, etc).

## Not using the Cloud Shell

Alternatively, you can configure the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install-sdk) 
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

## Summary of changes done to the project

The Terraform uses the modules of [Cloud Foundations Fabric (FAST)](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric), 
and the setup is done following the principle of least privilege and applying 
the recommendations given in the [Google Cloud Security Foundations blueprint](https://cloud.google.com/architecture/security-foundations)

The following resources are created with this Terraform code:

* A bucket of the same name as the project id, and the data in the subdirectory `data` uploaded to that bucket.
* A dataset in BigQuery with name `data_playground`, with a table of name `transactions` containing the data for the demo.
* Two custom service accounts: one for Vertex AI and one for Dataflow, with the right permissions to be used for those services.
* The custom Vertex AI service account has permissions to use and impersonate the custom Dataflow service account.
* The Vertex AI service agent account (created when you enable the Vertex API) has permissions to impersonate the custom Vertex AI service account.
* A subnetwork in the selected region, with [Google Private Access enabled](https://cloud.google.com/vpc/docs/configure-private-google-access).
* Some firewall rules preventing any machine in any other VPC or in Internet to reach the resources in your project
* A Cloud NAT to channel the output to Internet, should that be required by any project resource

## Data location

The directory `data/` contains a CSV file that you need to import as table 
in BigQuery in the dataset `data_playground`.

The Terraform code creates a bucket with the same name as your project id 
and uploads the CSV file to that bucket. 

After that, the CSV file is automatically imported into a table of name 
`transactions` in the dataset `data_playground`.
