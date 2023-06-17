module "mlops" {
  source = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//blueprints/data-solutions/vertex-mlops"

  #IMPORTANT: Choose an unique prefix
  prefix       = "YOUR_PREFIX"
  bucket_name  = "orbit1"
  dataset_name = "data_playground"
  notebooks    = {}
  #Provide 'billing_account_id' value if project creation is needed, uses existing 'project_id' if null
  project_config = {
    #billing_account_id = "000000-123456-123456"
    #parent             = "folders/111111111111"
    project_id = "orbit1"
  }
}
